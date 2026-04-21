from __future__ import annotations

import logging
import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

from .document_service import Document
from ..pipeline.preprocessing.text_normalizer import TextNormalizer
from ..pipeline.preprocessing.sentence_splitter import SentenceSplitter
from ..pipeline.preprocessing.tokenizer import Tokenizer
from ..pipeline.lsh.candidate_finder import (
    CandidateFinder,
    LSHConfig,
    MinHashConfig,
    ShingleConfig,
    Shingler,
)
from ..pipeline.gst.greedy_string_tiling import GreedyStringTiler
from ..pipeline.merging.passage_merger import PassageMatch, merge_overlapping_passages

try:
    from ..pipeline.pos_analysis.pos_tagger import POSTagger
    from ..pipeline.pos_analysis.pos_similarity import POSSimilarity
    POS_AVAILABLE = True
except (ImportError, RuntimeError):
    POS_AVAILABLE = False
    POSTagger = None
    POSSimilarity = None

from ..pipeline.similarity.edit_distance import EditDistance
from ..pipeline.stylometry.style_analyzer import StylometryAnalyzer
from ..utils.disjoint_set import DisjointSet

logger = logging.getLogger(__name__)


@dataclass
class PlagiarismConfig:
    """Configuration for the plagiarism detection pipeline.
    
    All thresholds and parameters are tuned for production use with
    typical lab report submissions (1,000 - 50,000 tokens per document).
    """

    # Shingling: k-word shingles. Higher k = more specific matches, fewer false positives.
    # For lab reports: k=3 balances specificity with coverage
    shingle_size: int = 3

    # MinHash: more permutations = higher accuracy but slower
    # 128 permutations gives ~1% error rate in Jaccard estimation
    minhash_perm: int = 128

    # LSH: threshold for candidate selection. Lower = more candidates (more comparisons)
    # 0.5 means: MinHash Jaccard >= 0.5 needed to be considered candidates
    # Conservative threshold to catch more potential plagiarism
    lsh_threshold: float = 0.4

    # GST: minimum tile/match length in tokens. 
    # 5 tokens = ~2-3 typical words, balances specificity vs. sensitivity
    # Minimum 3 tokens allowed for very short documents
    gst_min_match_length: int = 5

    # Raw text similarity threshold after edit distance.
    # 0.75 means: 75% textual match required (allows for minor edits)
    # Range: [0.7, 0.85] for production
    raw_similarity_threshold: float = 0.6

    # POS sequence similarity threshold.
    # 0.7 allows structural changes (paraphrasing) while finding similarities
    # Lower value (0.6) = more lenient, catches more paraphrases
    pos_similarity_threshold: float = 0.7

    def __post_init__(self) -> None:
        """Validate configuration parameters."""
        if self.shingle_size < 2 or self.shingle_size > 8:
            raise ValueError("shingle_size must be in [2, 8]")
        
        if self.minhash_perm < 64 or self.minhash_perm > 512:
            raise ValueError("minhash_perm must be in [64, 512]")
        
        if not (0.1 <= self.lsh_threshold <= 0.9):
            raise ValueError("lsh_threshold must be in [0.1, 0.9]")
        
        if self.gst_min_match_length < 3 or self.gst_min_match_length > 12:
            raise ValueError("gst_min_match_length must be in [3, 12]")
        
        if not (0.5 <= self.raw_similarity_threshold <= 0.95):
            raise ValueError("raw_similarity_threshold must be in [0.5, 0.95]")
        
        if not (0.5 <= self.pos_similarity_threshold <= 0.95):
            raise ValueError("pos_similarity_threshold must be in [0.5, 0.95]")


class PlagiarismDetector:
    """
    End-to-end plagiarism detection orchestrator.

    Implements the full 12-stage pipeline:
    1. Text preprocessing (normalization, tokenization)
    2. Shingling (k-word shingles)
    3. MinHash signature generation
    4. LSH candidate filtering
    5. Greedy String Tiling to find matching passages
    6. Extract suspicious passages
    7. Edit distance verification on raw text
    8. POS tagging for grammatical analysis
    9. Edit distance on POS sequences (detect paraphrasing)
    10. Stylometry analysis
    11. Merge overlapping passages
    12. Generate final plagiarism report

    This class wires all components together and implements the orchestration logic.
    """

    # Maximum document size to process (prevents memory/CPU exhaustion)
    MAX_DOCUMENT_SIZE = 5_000_000  # 5MB of text

    # Thresholds for valid document comparison
    MIN_TOKENS_FOR_COMPARISON = 3
    MIN_SHINGLES_FOR_CANDIDATE = 1

    def __init__(self, config: PlagiarismConfig | None = None) -> None:
        """Initialize the plagiarism detector with given configuration.
        
        Args:
            config: PlagiarismConfig instance. If None, uses defaults.
        
        Raises:
            ValueError: If config parameters are invalid.
        """
        self.config = config or PlagiarismConfig()
        
        logger.info(
            "Initializing PlagiarismDetector with config: "
            "shingle_size=%d, minhash_perm=%d, lsh_threshold=%.2f, "
            "gst_min_match_length=%d, raw_sim_threshold=%.2f, pos_sim_threshold=%.2f",
            self.config.shingle_size,
            self.config.minhash_perm,
            self.config.lsh_threshold,
            self.config.gst_min_match_length,
            self.config.raw_similarity_threshold,
            self.config.pos_similarity_threshold,
        )

        # Initialize preprocessing pipeline
        self.normalizer = TextNormalizer()
        self.splitter = SentenceSplitter()
        self.tokenizer = Tokenizer()

        # Initialize LSH candidate filtering (Stage 2-4)
        self.shingler = Shingler(
            ShingleConfig(size=self.config.shingle_size, max_shingles=100_000)
        )
        self.candidate_finder = CandidateFinder(
            minhash_config=MinHashConfig(num_perm=self.config.minhash_perm),
            lsh_config=LSHConfig(
                threshold=self.config.lsh_threshold,
                num_perm=self.config.minhash_perm,
            ),
        )

        # Initialize passage matching (Stage 5)
        adaptive_min_match = max(3, min(self.config.gst_min_match_length, 8))
        self.gst = GreedyStringTiler(min_match_length=adaptive_min_match)

        # Initialize POS analysis (Stage 8-9)
        # POS analysis is optional. If spaCy or its model is missing,
        # continue without POS scoring so the API can still start.
        if POS_AVAILABLE and POSTagger is not None:
            try:
                self.pos_tagger = POSTagger()
                self.pos_similarity = POSSimilarity(self.pos_tagger)
                logger.info("POS analysis enabled")
            except RuntimeError as exc:
                logger.warning("POS analysis disabled: %s", exc)
                self.pos_tagger = None
                self.pos_similarity = None
        else:
            logger.warning("POS analysis not available (spaCy not installed)")
            self.pos_tagger = None
            self.pos_similarity = None
        
        # Initialize similarity scoring (Stage 7)
        self.edit_distance = EditDistance()
        
        # Initialize stylometry analysis (Stage 10)
        self.stylometry = StylometryAnalyzer()
        
        logger.info("PlagiarismDetector initialized successfully")

    def _preprocess_document(self, doc: Document) -> Tuple[str, List[str]]:
        """Normalize and tokenize the document content.
        
        STAGE 1: TEXT PREPROCESSING
        - Unicode normalization
        - Lowercase conversion
        - Whitespace normalization
        - Sentence segmentation
        - Word tokenization
        
        Args:
            doc: Document object with id and content.
        
        Returns:
            Tuple of (normalized_text, token_list)
        
        Raises:
            TypeError: If doc is not a Document instance.
            ValueError: If document content is too large or invalid.
        """
        if not isinstance(doc, Document):
            raise TypeError(f"Expected Document, got {type(doc)}")

        # Validate document content
        if not isinstance(doc.content, str):
            raise ValueError(f"Document content must be string, got {type(doc.content)}")

        if len(doc.content) > self.MAX_DOCUMENT_SIZE:
            logger.warning(
                "Document %s exceeds max size (%d > %d bytes). Truncating.",
                doc.id,
                len(doc.content),
                self.MAX_DOCUMENT_SIZE,
            )
            content = doc.content[:self.MAX_DOCUMENT_SIZE]
        else:
            content = doc.content

        # Stage 1: Normalize text
        normalized = self.normalizer.normalize(content)

        # Stage 1: Split into sentences
        sentences = self.splitter.split(normalized)

        # Stage 1: Tokenize sentences
        tokens: List[str] = []
        for sentence in sentences:
            sentence_tokens = self.tokenizer.tokenize(sentence)
            tokens.extend(sentence_tokens)

        # Log preprocessing results
        logger.debug(
            "Preprocessed document %s: %d chars -> %d tokens (%d sentences)",
            doc.id,
            len(normalized),
            len(tokens),
            len(sentences),
        )

        return normalized, tokens

    def _build_shingles(self, docs: Iterable[Document]) -> Dict[str, Iterable[str]]:
        """Compute shingles for each document.
        
        STAGE 2: SHINGLING
        - Convert tokenized text into k-word shingles
        - Filter out documents with insufficient content
        
        Args:
            docs: Iterable of Document objects.
        
        Returns:
            Dict mapping document_id -> set of shingles.
            Documents with too few tokens are excluded.
        """
        result: Dict[str, Iterable[str]] = {}
        
        for doc in docs:
            try:
                _, tokens = self._preprocess_document(doc)

                # Skip documents that are too short for shingling
                if len(tokens) < self.config.shingle_size:
                    logger.debug(
                        "Document %s too short for shingling: %d tokens (need >= %d)",
                        doc.id,
                        len(tokens),
                        self.config.shingle_size,
                    )
                    continue

                shingles = self.shingler.shingles(tokens)
                
                if not shingles:
                    logger.debug("Document %s produced no shingles", doc.id)
                    continue

                result[doc.id] = shingles
                logger.debug(
                    "Generated shingles for %s: %d unique shingles from %d tokens",
                    doc.id,
                    len(shingles),
                    len(tokens),
                )
            except Exception as e:
                logger.error("Failed to build shingles for document %s: %s", doc.id, e)
                continue

        logger.info(
            "Built shingles for %d/%d documents (threshold: >= %d tokens)",
            len(result),
            sum(1 for _ in docs),
            self.config.shingle_size,
        )
        
        return result

    def detect(self, documents: Iterable[Document]) -> Dict[str, List]:
        """
        Run the full plagiarism detection pipeline.

        FULL PIPELINE:
        1. Preprocess: normalize and tokenize all documents
        2. Shingling: extract k-word shingles
        3. MinHash: create signatures
        4. LSH: find candidate document pairs
        5. GST: find longest matching passages in candidates
        6. Extract: isolate suspicious passages
        7. Edit Distance: verify similarity on raw text
        8. POS Tagging: analyze grammatical structure
        9. POS Edit Distance: detect paraphrasing
        10. Stylometry: analyze writing style
        11. Merge: combine overlapping passages
        12. Report: generate final plagiarism scores

        Args:
            documents: Iterable of Document objects to compare.

        Returns:
            Dict mapping document_id -> [doc_id, doc_group, plagiarism_score]
            where doc_group maps target_doc_id -> [passages_list, similarity_score]
        """
        logger.info("=" * 100)
        logger.info("🔍 STARTING PLAGIARISM DETECTION PIPELINE")
        logger.info("=" * 100)
        docs_list = list(documents)
        
        # Validate inputs
        if len(docs_list) < 2:
            logger.warning("Insufficient documents for comparison: %d (need >= 2)", len(docs_list))
            return {}

        logger.info("📊 Comparing %d documents", len(docs_list))
        for doc in docs_list:
            logger.info("  - Document ID: %s, Content length: %d chars", doc.id, len(doc.content))
        doc_map: Dict[str, Document] = {d.id: d for d in docs_list}

        # STAGE 10: Stylometry analysis - analyze writing style for all documents
        logger.debug("Stage 10: Analyzing stylometry...")
        stylometry_map: Dict[str, Dict[str, float]] = {}
        for doc_id, doc in doc_map.items():
            try:
                stylometry_map[doc_id] = self.stylometry.analyze(doc.content)
                logger.debug("  Stylometry for %s: %s", doc_id, stylometry_map[doc_id])
            except Exception as e:
                logger.warning("Failed to analyze stylometry for %s: %s", doc_id, e)
                stylometry_map[doc_id] = {}

        # STAGES 2-4: Shingling, MinHash, LSH - find candidate pairs 
        logger.info("\n" + "=" * 100)
        logger.info("⚙️  STAGE 2: SHINGLING - Building k-word shingles...")
        logger.info("=" * 100)
        shingles_by_doc = self._build_shingles(docs_list)

        if not shingles_by_doc:
            logger.error("No documents produced shingles. Aborting detection.")
            return {doc.id: [doc.id, {}, 0.0] for doc in docs_list}

        logger.debug("Stage 3-4: Finding LSH candidates from %d documents with shingles", len(shingles_by_doc))
        candidates = self.candidate_finder.find_candidates(shingles_by_doc)
        
        if not candidates:
            logger.warning("No candidate pairs found via LSH")
            return {doc.id: [doc.id, {}, 0.0] for doc in docs_list}

        logger.info("\n" + "=" * 100)
        logger.info("🔗 STAGE 3-4: LSH CANDIDATE FINDING")
        logger.info("=" * 100)
        logger.info("Found %d candidate document pairs via LSH (%.1f%% of O(n²))",
            len(candidates),
            len(candidates) / (len(docs_list) * (len(docs_list) - 1) / 2) * 100
            if len(docs_list) > 1 else 0,
        )
        for i, (doc_a, doc_b, approx_jaccard) in enumerate(candidates[:5]):
            logger.info("  Candidate %d: %s <-> %s (Jaccard≈%.3f)", i+1, doc_a, doc_b, approx_jaccard)
        if len(candidates) > 5:
            logger.info("  ... and %d more candidate pairs", len(candidates) - 5)

        # Stage 1: Preprocess all documents once
        logger.info("\n" + "=" * 100)
        logger.info("📝 STAGE 1: PREPROCESSING - Normalizing and tokenizing...")
        logger.info("=" * 100)
        preprocessed: Dict[str, Tuple[str, List[str]]] = {}
        for doc_id, doc in doc_map.items():
            try:
                preprocessed[doc_id] = self._preprocess_document(doc)
            except Exception as e:
                logger.error("Failed to preprocess document %s: %s", doc_id, e)
                preprocessed[doc_id] = ("", [])

        logger.info("✅ Preprocessing complete:")
        for doc_id, (normalized, tokens) in preprocessed.items():
            logger.info("  %s: %d normalized chars, %d tokens", doc_id, len(normalized), len(tokens))

        all_passages: List[PassageMatch] = []

        # Stage 5-9: Process each candidate pair
        logger.info("\n" + "=" * 100)
        logger.info("🔏 STAGE 5-9: PASSAGE DETECTION (GST) & VERIFICATION")
        logger.info("=" * 100)
        logger.debug("Processing %d candidate pairs with GST and verification...", len(candidates))
        tiles_found = 0
        gst_filtered = 0
        raw_sim_filtered = 0
        pos_sim_filtered = 0
        
        for candidate_idx, (doc_a, doc_b, approx_jaccard) in enumerate(candidates):
            if approx_jaccard <= 0:
                logger.debug("Skipping candidate (%s, %s): Jaccard %.3f <= 0", doc_a, doc_b, approx_jaccard)
                continue

            norm_a, tokens_a = preprocessed.get(doc_a, ("", []))
            norm_b, tokens_b = preprocessed.get(doc_b, ("", []))
            
            if not tokens_a or not tokens_b:
                logger.debug("Skipping candidate (%s, %s): empty token sequence", doc_a, doc_b)
                continue

            logger.info("\n📍 Processing Candidate %d/%d: %s <-> %s (Jaccard≈%.3f)", 
                       candidate_idx + 1, len(candidates), doc_a, doc_b, approx_jaccard)
            logger.info("  Tokens: %d vs %d", len(tokens_a), len(tokens_b))

            # Stage 5: Greedy String Tiling
            tiles = self.gst.find_tiles(tokens_a, tokens_b)
            if not tiles:
                logger.info("  ❌ No tiles found by GST")
                gst_filtered += 1
                continue

            logger.info("  ✓ GST found %d tiles", len(tiles))
            tiles_found += len(tiles)

            # Process each tile
            for tile in tiles:
                try:
                    # Stage 6: Extract suspicious passages
                    source_start = self._approx_char_offset(tokens_a, tile.src_start)
                    source_end = self._approx_char_offset(tokens_a, tile.src_end)
                    target_start = self._approx_char_offset(tokens_b, tile.dst_start)
                    target_end = self._approx_char_offset(tokens_b, tile.dst_end)
                    
                    # Validate bounds
                    source_start = max(0, min(source_start, len(norm_a)))
                    source_end = max(source_start, min(source_end, len(norm_a)))
                    target_start = max(0, min(target_start, len(norm_b)))
                    target_end = max(target_start, min(target_end, len(norm_b)))
                    
                    seg_a = norm_a[source_start:source_end]
                    seg_b = norm_b[target_start:target_end]

                    if not seg_a or not seg_b:
                        logger.debug("Empty passage after extraction; skipping")
                        continue
                    
                    # Stage 7: Edit distance on raw text
                    raw_sim = self.edit_distance.raw_text_similarity(seg_a, seg_b)
                    logger.debug("    Tile[%d-%d vs %d-%d]: raw_similarity = %.4f", 
                                tile.src_start, tile.src_end, tile.dst_start, tile.dst_end, raw_sim)
                    
                    if raw_sim < self.config.raw_similarity_threshold:
                        logger.debug("      ❌ FILTERED by raw_sim threshold (%.4f < %.4f)", 
                                    raw_sim, self.config.raw_similarity_threshold)
                        raw_sim_filtered += 1
                        continue

                    # Stage 9: Edit distance on POS sequences
                    if self.pos_similarity is None:
                        # POS analysis unavailable; use neutral score
                        pos_sim = 1.0
                        logger.debug("      ⚠️  POS analysis unavailable, using neutral score 1.0")
                    else:
                        pos_sim = self.pos_similarity.similarity(seg_a, seg_b)
                        logger.debug("      pos_similarity = %.4f", pos_sim)
                    
                    if pos_sim < self.config.pos_similarity_threshold:
                        logger.debug("      ❌ FILTERED by pos_sim threshold (%.4f < %.4f)", 
                                    pos_sim, self.config.pos_similarity_threshold)
                        pos_sim_filtered += 1
                        continue

                    # All checks passed! Record this passage match
                    logger.info("      ✅ PASSAGE ACCEPTED! raw_sim=%.4f, pos_sim=%.4f, passage_len=%d chars", 
                               raw_sim, pos_sim, len(seg_a))
                    all_passages.append(
                        PassageMatch(
                            source_doc_id=doc_a,
                            target_doc_id=doc_b,
                            source_start=source_start,
                            source_end=source_end,
                            target_start=target_start,
                            target_end=target_end,
                            similarity=float(raw_sim),
                            pos_similarity=float(pos_sim),
                        )
                    )

                except Exception as e:
                    logger.warning("Error processing tile for (%s, %s): %s", doc_a, doc_b, e)
                    continue

        logger.info(
            "\n📊 PASSAGE VERIFICATION SUMMARY:"
        )
        logger.info(
            "  Total tiles found: %d | Fixed by GST: %d | Filtered by raw_sim: %d | Filtered by pos_sim: %d",
            tiles_found, gst_filtered, raw_sim_filtered, pos_sim_filtered
        )
        logger.info("  ✅ Total ACCEPTED passages: %d", len(all_passages))

        # Stage 11: Merge overlapping passages
        logger.info("\n" + "=" * 100)
        logger.info("🔗 STAGE 11: MERGING - Combining overlapping passages (max_gap=5)...")
        logger.info("=" * 100)
        logger.debug("Merging %d detected passages...", len(all_passages))
        merged = merge_overlapping_passages(all_passages, max_gap=5)
        logger.info("✅ Merged %d passages into %d groups", len(all_passages), len(merged))
        
        for i, merged_p in enumerate(merged[:5]):
            logger.debug("  Merged group %d: %s vs %s, chars %d-%d, sim=%.4f, pos_sim=%.4f",
                        i+1, merged_p.source_doc_id, merged_p.target_doc_id, 
                        merged_p.source_start, merged_p.source_end, 
                        merged_p.similarity, merged_p.pos_similarity)

        # Stage 12: Generate reports
        logger.info("\n" + "=" * 100)
        logger.info("📋 STAGE 12: REPORT GENERATION - Computing final similarity scores...")
        logger.info("=" * 100)
        reports = self._build_reports(doc_map, merged, stylometry_map)
        
        logger.info("Plagiarism detection completed successfully")
        return reports

    @staticmethod
    def _approx_char_offset(tokens: List[str], token_index: int) -> int:
        """Approximate character offset in a space-joined string.
        
        Converts token index to approximate character position assuming
        tokens are joined with single spaces.
        
        FIXED: Corrected off-by-one error that was causing passages to not cover
        the complete document.
        
        Example:
            tokens = ["hello", "world", "foo"]
            _approx_char_offset(tokens, 0) = 0      # "hello" starts at char 0
            _approx_char_offset(tokens, 1) = 6      # "world" starts at char 6 (5 + 1 space)
            _approx_char_offset(tokens, 2) = 12     # "foo" starts at char 12
            _approx_char_offset(tokens, 3) = 15     # past end
        
        Args:
            tokens: List of token strings
            token_index: Token index to convert
        
        Returns:
            Approximate character offset (0-based)
        """
        if not isinstance(tokens, (list, tuple)):
            raise TypeError("tokens must be a sequence")
        
        if not isinstance(token_index, int):
            raise TypeError("token_index must be an integer")

        # Clamp to valid range
        if token_index <= 0:
            return 0
        
        # For past-end, return position after all tokens
        if token_index >= len(tokens):
            # All token lengths + (number of tokens - 1) spaces
            return sum(len(t) for t in tokens) + len(tokens) - 1

        # Position of token_index = sum of lengths before + token_index spaces
        # (there are token_index spaces before token_index when starting from position 0)
        return sum(len(t) for t in tokens[:token_index]) + token_index

    def _stylometry_similarity(
        self,
        s1: Dict[str, float],
        s2: Dict[str, float]
    ) -> float:
        """Compute stylometry similarity between two documents.
        
        Compares writing style features:
        - Average sentence length
        - Sentence length variance
        - Type-token ratio (vocabulary richness)
        - Function word frequency
        - Punctuation usage
        
        Uses Euclidean distance between feature vectors.
        
        Args:
            s1: Stylometry features of document 1
            s2: Stylometry features of document 2
        
        Returns:
            Similarity score [0, 1] where 1.0 = identical styles, 0.0 = very different
        """
        features = [
            "avg_sentence_length",
            "std_sentence_length",
            "type_token_ratio",
            "function_word_ratio",
            "punctuation_ratio"
        ]
        
        # Compute Euclidean distance between feature vectors
        dist = 0.0
        for f in features:
            v1 = float(s1.get(f, 0.0))
            v2 = float(s2.get(f, 0.0))
            # Clamp to valid ranges
            v1 = max(0.0, min(1.0, v1))
            v2 = max(0.0, min(1.0, v2))
            dist += (v1 - v2) ** 2
        
        dist = math.sqrt(dist)
        
        # Maximum possible distance in feature space
        # Assuming all features are in [0, 1], worst case is all features differ by 1.0
        max_possible = math.sqrt(len(features) * (1.0 ** 2))
        
        if max_possible == 0:
            similarity = 1.0
        else:
            similarity = 1.0 - (dist / max_possible)
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, similarity))

    def _compute_doc_similarity(
        self,
        passages: List[Dict],
        doc_length: int,
        stylometry_sim: float,
    ) -> float:
        """Compute document-level similarity score.
        
        Combines:
        - Passage-level text similarity (edit distance on raw text)
        - Structural similarity (edit distance on POS sequences)
        - Writing style similarity (stylometry features)
        
        Weighting:
        - 50% passage text similarity
        - 30% passage POS similarity
        - 20% stylometry similarity
        
        Args:
            passages: List of passage matches with similarity scores
            doc_length: Total characters in the document
            stylometry_sim: Pre-computed stylometry similarity [0, 1]
        
        Returns:
            Combined similarity score [0, 1]
        """
        # Weight components
        alpha = 0.6   # raw text similarity weight
        beta = 0.3    # POS similarity weight
        gamma = 0.1   # stylometry similarity weight

        # Ensure safe denominator
        doc_length = max(doc_length, 1)

        # Compute weighted similarity from passages
        passage_score = 0.0
        for p in passages:
            # Validate passage data
            if not isinstance(p, dict):
                logger.warning("Invalid passage data: %s", p)
                continue
            
            passage_length = p.get("source_end", 0) - p.get("source_start", 0)
            if passage_length <= 0:
                continue

            raw_sim = float(p.get("similarity", 0.0))
            pos_sim = float(p.get("pos_similarity", 0.0))

            # Normalize to [0, 1]
            raw_sim = max(0.0, min(1.0, raw_sim))
            pos_sim = max(0.0, min(1.0, pos_sim))

            # Weighted contribution of this passage
            contribution = (passage_length / doc_length) * (alpha * raw_sim + beta * pos_sim)
            passage_score += contribution

        # Final score: passages + stylometry influence
        final_score = passage_score + gamma * stylometry_sim

        # Clamp to [0, 1]
        return max(0.0, min(1.0, final_score))
    
    @staticmethod
    def _empty_report(doc_id: str) -> Dict:
        return {"document_id": doc_id, "plagiarism_score": 0.0, "matched_passages": []}

    def _build_reports(
        self,
        docs: Dict[str, Document],
        passages: Iterable[PassageMatch],
        stylometry_map: Dict[str, Dict[str, float]],
    ) -> Dict[str, List]:
        """Aggregate passages into per-document reports with grouped matches (bidirectional).
        
        STAGE 12: REPORT GENERATION
        - Build bidirectional passage groupings
        - Compute per-document similarity scores
        - Calculate overall plagiarism percentage
        - Handle edge cases (no matches, empty documents)
        
        Args:
            docs: Map of document_id -> Document
            passages: Detected passage matches
            stylometry_map: Pre-computed stylometry features per document
        
        Returns:
            Dict mapping document_id -> [doc_id, doc_group, plagiarism_score]
        """
        logger.debug("Building plagiarism reports for %d documents", len(docs))

        # 🔥 STEP 1: Build bidirectional grouping
        grouped: Dict[str, Dict[str, List[PassageMatch]]] = {}

        for p in passages:
            # Source → Target
            grouped.setdefault(p.source_doc_id, {}).setdefault(p.target_doc_id, []).append(p)

            # Target → Source (swap positions correctly for bidirectional comparison)
            grouped.setdefault(p.target_doc_id, {}).setdefault(p.source_doc_id, []).append(
                PassageMatch(
                    source_doc_id=p.target_doc_id,
                    target_doc_id=p.source_doc_id,
                    source_start=p.target_start,
                    source_end=p.target_end,
                    target_start=p.source_start,
                    target_end=p.source_end,
                    similarity=p.similarity,
                    pos_similarity=p.pos_similarity,
                )
            )
        
        logger.info("\n📍 REPORT BUILDING - Processing similarity calculations:")
        logger.info("=" * 100)

        # 🔥 STEP 2: Build reports for each document
        reports: Dict[str, List] = {}

        for doc_id in docs.keys():
            doc_group: Dict[str, List] = {}

            # Calculate safe document length (avoid division by zero)
            doc_content = docs[doc_id].content or ""
            doc_length = max(len(doc_content), 1)

            logger.info("\n📄 Document: %s (length=%d chars)", doc_id, doc_length)

            if doc_id in grouped:
                for target_doc_id, passage_list in grouped[doc_id].items():
                    # Build passage list with full similarity info
                    passages_list = [
                        {
                            "source_start": p.source_start,
                            "source_end": p.source_end,
                            "target_start": p.target_start,
                            "target_end": p.target_end,
                            "similarity": p.similarity,
                            "pos_similarity": p.pos_similarity,
                        }
                        for p in passage_list
                    ]

                    # Compute stylometry similarity between this document and target
                    stylometry_sim = self._stylometry_similarity(
                        stylometry_map.get(doc_id, {}),
                        stylometry_map.get(target_doc_id, {}),
                    )

                    # Compute overall similarity score for this document pair
                    similarity_score = self._compute_doc_similarity(
                        passages_list,
                        doc_length,
                        stylometry_sim,
                    )

                    doc_group[target_doc_id] = [
                        passages_list,
                        similarity_score,
                    ]

                    logger.debug(
                        "  vs %s: %d passages, similarity=%.3f, stylometry=%.3f",
                        target_doc_id, len(passages_list), similarity_score, stylometry_sim
                    )

            # 🔥 Ensure all documents appear in comparisons (even if 0 similarity)
            for other_doc_id in docs.keys():
                if other_doc_id != doc_id and other_doc_id not in doc_group:
                    doc_group[other_doc_id] = [[], 0.0]

            # 🔥 STEP 3: Overall plagiarism score from merged passages
            all_passages_flat = []
            for target_doc_id, (passages_list, _) in doc_group.items():
                all_passages_flat.extend(passages_list)

            logger.debug("  📊 Calculating final plagiarism score from %d total passages", len(all_passages_flat))

            # Convert to PassageMatch for merging within this document
            passages_for_merge = [
                PassageMatch(
                    source_doc_id=doc_id,
                    target_doc_id="dummy",
                    source_start=p["source_start"],
                    source_end=p["source_end"],
                    target_start=0,
                    target_end=0,
                    similarity=p["similarity"],
                    pos_similarity=p["pos_similarity"],
                )
                for p in all_passages_flat
            ]

            # Merge overlapping passages within this document
            merged_passages = merge_overlapping_passages(passages_for_merge, max_gap=0)
            logger.debug("  📊 After merging: %d passage groups", len(merged_passages))

            # Compute score from merged passages
            # Weights: 60% raw text similarity, 40% POS sequence similarity
            y_weight = 0.6  # raw edit similarity weight
            z_weight = 0.4  # pos similarity weight
            
            plagiarism_score = 0.0
            total_plagiarized_chars = 0
            
            logger.debug("  📋 SCORE CALCULATION BREAKDOWN (y_weight=%.2f, z_weight=%.2f):", y_weight, z_weight)
            logger.debug("  Overall doc_length: %d chars", doc_length)
            
            for idx, mp in enumerate(merged_passages):
                k = mp.source_end - mp.source_start  # characters in this plagiarized passage
                edit_sim = mp.similarity
                pos_sim = mp.pos_similarity
                
                # Weighted combination: more weight on actual textual match
                passage_contribution = (k / doc_length) * (y_weight * edit_sim + z_weight * pos_sim)
                plagiarism_score += passage_contribution
                total_plagiarized_chars += k
                
                logger.debug(
                    "    Passage %d: chars[%d-%d] (len=%d) | raw_sim=%.4f | pos_sim=%.4f | "
                    "weight=%.4f | contribution=%.6f",
                    idx + 1, mp.source_start, mp.source_end, k, edit_sim, pos_sim, 
                    k / doc_length, passage_contribution
                )

            # Convert to percentage (0-100 scale)
            overall_plagiarism_score = plagiarism_score * 100.0
            overall_plagiarism_score = min(100.0, max(0.0, overall_plagiarism_score))
            
            logger.info(
                "  ✅ FINAL RESULT - Raw score: %.6f → Percentage: %.2f%% | Total plagiarized: %d/%d chars",
                plagiarism_score, overall_plagiarism_score, total_plagiarized_chars, doc_length
            )

            reports[doc_id] = [
                doc_id,
                doc_group,
                round(overall_plagiarism_score, 2),
            ]

            logger.info(
                "Document %s: plagiarism_score=%.2f%% (%d/%d chars from %d targets)",
                doc_id,
                overall_plagiarism_score,
                total_plagiarized_chars,
                doc_length,
                len([t for t in doc_group if doc_group[t][1] > 0]),
            )
            

        # STEP 4: Enforce symmetric similarity between document pairs
        logger.info("\n" + "=" * 100)
        logger.info("[SYMMETRY] ENFORCING SYMMETRIC SIMILARITY - Ensuring consistency between document pairs...")
        logger.info("=" * 100)
        self._enforce_symmetric_similarity(reports)

        logger.info("\n" + "=" * 100)
        logger.info("[SUCCESS] PLAGIARISM DETECTION COMPLETED SUCCESSFULLY")
        logger.info("=" * 100)
        logger.info("[SUMMARY] FINAL RESULTS (after symmetry enforcement):")
        for doc_id, (_, doc_group, score) in reports.items():
            for target_id, (_, sim) in doc_group.items():
                if sim > 0:
                    logger.info("  %s vs %s: %.2f%% similarity", doc_id, target_id, sim)
        logger.info("=" * 100) 
        
        
        
        return reports

    def _enforce_symmetric_similarity(self, reports: Dict[str, List]) -> None:
        """Enforce symmetric similarity scores between document pairs.
        
        For every pair (docA, docB), ensures:
            reports[A].doc_group[B].similarity =
            reports[B].doc_group[A].similarity =
            max(sim_AB, sim_BA)
        
        This prevents inconsistencies and ensures stable clustering results.
        
        Example:
            Before: doc1 → doc2 = 0.80, doc2 → doc1 = 0.85
            After:  doc1 → doc2 = 0.85, doc2 → doc1 = 0.85
        
        Modifies reports in-place. Only updates similarity scores; passages remain unchanged.
        
        Args:
            reports: Dict mapping document_id -> [doc_id, doc_group, plagiarism_score]
                     where doc_group[target_id] = [passages_list, similarity_score]
        """
        logger.debug("[SYMMETRY] Enforcing symmetric similarity across %d documents...", len(reports))
        processed_pairs = set()
        updates_count = 0
        
        for doc_a, (_, group_a, _) in reports.items():
            for doc_b, (passages_a, sim_ab) in group_a.items():
                # Skip if already processed (avoid duplicate work)
                if (doc_a, doc_b) in processed_pairs or (doc_b, doc_a) in processed_pairs:
                    continue
                
                # Mark as processed
                processed_pairs.add((doc_a, doc_b))
                
                # Check if reverse pair exists
                if doc_b not in reports or doc_a not in reports[doc_b][1]:
                    logger.debug(
                        "  [WARN] Reverse pair (%s, %s) not found in reports; skipping",
                        doc_b, doc_a
                    )
                    continue
                
                # Get reverse similarity
                passages_b, sim_ba = reports[doc_b][1][doc_a]
                
                # Compute maximum similarity
                max_sim = max(sim_ab, sim_ba)
                
                # Update both directions if changed
                if abs(max_sim - sim_ab) > 1e-6 or abs(max_sim - sim_ba) > 1e-6:
                    logger.debug(
                        "  [PAIR] (%s, %s): [%.4f, %.4f] -> max(%.4f) = symmetric [%.4f, %.4f]",
                        doc_a, doc_b, sim_ab, sim_ba, max_sim, max_sim, max_sim
                    )
                    
                    # Update both directions to maximum
                    reports[doc_a][1][doc_b][1] = max_sim
                    reports[doc_b][1][doc_a][1] = max_sim
                    updates_count += 1
        
        logger.info("[SUCCESS] Symmetric similarity enforcement complete: %d pairs synchronized", updates_count)

    def find_similar_document_clusters(
        self,
        reports: Dict[str, List],
        threshold: float
    ) -> List[List[str]]:
        """Find clusters of documents with similarity >= threshold using DSU."""
        dsu = DisjointSet(reports.keys())

        for doc_id, (_, doc_group, _) in reports.items():
            for target_doc_id, (_, similarity_score) in doc_group.items():
                if similarity_score >= threshold:
                    if doc_id < target_doc_id and similarity_score >= threshold:
                        dsu.union(doc_id, target_doc_id)

        from collections import defaultdict
        clusters_map = defaultdict(list)
        for doc_id in reports.keys():
            root = dsu.find(doc_id)
            clusters_map[root].append(doc_id)

        clusters = [sorted(cluster) for cluster in clusters_map.values() if len(cluster) >= 2]
        return clusters


__all__ = ["PlagiarismConfig", "PlagiarismDetector"]