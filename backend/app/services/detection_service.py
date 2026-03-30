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
    """Configuration for the plagiarism detection pipeline."""

    shingle_size: int = 3
    minhash_perm: int = 128
    lsh_threshold: float = 0.5
    gst_min_match_length: int = 5
    raw_similarity_threshold: float = 0.75
    pos_similarity_threshold: float = 0.8


class PlagiarismDetector:
    """
    End-to-end plagiarism detection orchestrator.

    Wires preprocessing, LSH candidate generation, GST, and scoring.
    """

    def __init__(self, config: PlagiarismConfig | None = None) -> None:
        self.config = config or PlagiarismConfig()

        self.normalizer = TextNormalizer()
        self.splitter = SentenceSplitter()
        self.tokenizer = Tokenizer()

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

        self.gst = GreedyStringTiler(
            min_match_length=self.config.gst_min_match_length
        )

        # POS analysis is optional. If spaCy or its model is missing,
        # continue without POS scoring so the API can still start.
        if POS_AVAILABLE and POSTagger is not None:
            try:
                self.pos_tagger = POSTagger()
                self.pos_similarity = POSSimilarity(self.pos_tagger)
            except RuntimeError as exc:
                logger.warning("POS analysis disabled: %s", exc)
                self.pos_tagger = None
                self.pos_similarity = None
        else:
            self.pos_tagger = None
            self.pos_similarity = None
        
        self.edit_distance = EditDistance()
        self.stylometry = StylometryAnalyzer()

    def _preprocess_document(self, doc: Document) -> Tuple[str, List[str]]:
        """Normalize and tokenize the document content."""
        if not isinstance(doc, Document):
            raise TypeError("doc must be a Document")

        normalized = self.normalizer.normalize(doc.content)
        sentences = self.splitter.split(normalized)
        tokens: List[str] = []
        for s in sentences:
            tokens.extend(self.tokenizer.tokenize(s))
        return normalized, tokens

    def _build_shingles(self, docs: Iterable[Document]) -> Dict[str, Iterable[str]]:
        """Compute shingles for each document."""
        result: Dict[str, Iterable[str]] = {}
        for doc in docs:
            _, tokens = self._preprocess_document(doc)
            shingles = self.shingler.shingles(tokens)
            if shingles:
                result[doc.id] = shingles
        return result

    def detect(self, documents: Iterable[Document]) -> Dict[str, List]:
        """
        Run the full plagiarism detection pipeline.

        Returns mapping of document_id -> [doc_id, doc_group, plagiarism_score].
        """
        docs_list = list(documents)
        if len(docs_list) < 2:
            return {}

        doc_map: Dict[str, Document] = {d.id: d for d in docs_list}

        stylometry_map: Dict[str, Dict[str, float]] = {
            doc_id: self.stylometry.analyze(doc.content)
            for doc_id, doc in doc_map.items()
        }

        shingles_by_doc = self._build_shingles(docs_list)
        candidates = self.candidate_finder.find_candidates(shingles_by_doc)

        if not candidates:
            return {doc.id: [doc.id, {}, 0.0] for doc in docs_list}

        preprocessed: Dict[str, Tuple[str, List[str]]] = {}
        for doc_id, doc in doc_map.items():
            preprocessed[doc_id] = self._preprocess_document(doc)

        all_passages: List[PassageMatch] = []

        for doc_a, doc_b, approx_sim in candidates:
            if approx_sim <= 0:
                continue

            norm_a, tokens_a = preprocessed.get(doc_a, ("", []))
            norm_b, tokens_b = preprocessed.get(doc_b, ("", []))
            if not tokens_a or not tokens_b:
                continue

            tiles = self.gst.find_tiles(tokens_a, tokens_b)
            for tile in tiles:
                source_start = self._approx_char_offset(tokens_a, tile.src_start)
                source_end = self._approx_char_offset(tokens_a, tile.src_end)

                target_start = self._approx_char_offset(tokens_b, tile.dst_start)
                target_end = self._approx_char_offset(tokens_b, tile.dst_end)
                
                seg_a = norm_a[source_start:source_end]
                seg_b = norm_b[target_start : target_end]
                
                raw_sim = self.edit_distance.raw_text_similarity(seg_a, seg_b)
                if raw_sim < self.config.raw_similarity_threshold:
                    continue

                # If POS analysis is unavailable, treat POS similarity as neutral.
                if self.pos_similarity is None:
                    pos_sim = 1.0
                else:
                    pos_sim = self.pos_similarity.similarity(seg_a, seg_b)
                if pos_sim < self.config.pos_similarity_threshold:
                    continue

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

        merged = merge_overlapping_passages(all_passages, max_gap=5)
        return self._build_reports(doc_map, merged, stylometry_map)

    @staticmethod
    def _approx_char_offset(tokens: List[str], token_index: int) -> int:
        """Approximate character offset in a space-joined string."""
        if token_index <= 0:
            return 0
        if token_index > len(tokens):
            token_index = len(tokens)
        return sum(len(t) + 1 for t in tokens[:token_index])

    def _stylometry_similarity(
        self,
        s1: Dict[str, float],
        s2: Dict[str, float]
    ) -> float:
        """Compute stylometry similarity using Euclidean distance."""
        features = [
            "avg_sentence_length",
            "std_sentence_length",
            "type_token_ratio",
            "function_word_ratio",
            "punctuation_ratio"
        ]
        dist = 0.0
        for f in features:
            dist += (s1.get(f, 0.0) - s2.get(f, 0.0)) ** 2
        dist = math.sqrt(dist)
        max_possible = math.sqrt(len(features))  # assuming values in [0,1]
        similarity = 1.0 - (dist / max_possible)
        return max(0.0, min(1.0, similarity))

    def _compute_doc_similarity(
        self,
        passages: List[Dict],
        doc_length: int,
        stylometry_sim: float,
    ) -> float:
        """Compute document-level similarity score."""
        alpha = 0.5
        beta = 0.3
        gamma = 0.2

        doc_length = max(doc_length, 1)  # ✅ safety

        score = 0.0
        for p in passages:
            # ✅ use correct field
            k = p["source_end"] - p["source_start"]

            raw_sim = p["similarity"]
            pos_sim = p["pos_similarity"]

            score += (k / doc_length) * (alpha * raw_sim + beta * pos_sim)

        final_score = score + gamma * stylometry_sim
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
        """Aggregate passages into per-document reports with grouped matches (bidirectional)."""

        # 🔥 STEP 1: Build bidirectional grouping
        grouped: Dict[str, Dict[str, List[PassageMatch]]] = {}

        for p in passages:
            # Source → Target
            grouped.setdefault(p.source_doc_id, {}).setdefault(p.target_doc_id, []).append(p)

            # Target → Source (swap positions correctly)
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

        # 🔥 STEP 2: Build reports
        reports: Dict[str, List] = {}

        for doc_id in docs.keys():
            doc_group: Dict[str, List] = {}

            # Safe doc length
            doc_length = max(len(docs[doc_id].content), 1)

            if doc_id in grouped:
                for target_doc_id, passage_list in grouped[doc_id].items():

                    # 🔥 Build passage list with full info
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

                    # 🔥 Stylometry similarity (doc ↔ target_doc)
                    stylometry_sim = self._stylometry_similarity(
                        stylometry_map.get(doc_id, {}),
                        stylometry_map.get(target_doc_id, {}),
                    )

                    # 🔥 Compute similarity score
                    similarity_score = self._compute_doc_similarity(
                        passages_list,
                        doc_length,
                        stylometry_sim,
                    )

                    doc_group[target_doc_id] = [
                        passages_list,
                        similarity_score,
                    ]

            # 🔥 STEP 3: Overall plagiarism score based on merged passages
            all_passages_flat = []
            for target_doc_id, (passages_list, _) in doc_group.items():
                all_passages_flat.extend(passages_list)

            # Convert to PassageMatch for merging
            passages_for_merge = [
                PassageMatch(
                    source_doc_id=doc_id,
                    target_doc_id="dummy",  # dummy target for merging
                    source_start=p["source_start"],
                    source_end=p["source_end"],
                    target_start=0,  # not used
                    target_end=0,   # not used
                    similarity=p["similarity"],
                    pos_similarity=p["pos_similarity"],
                )
                for p in all_passages_flat
            ]

            # Merge overlapping passages
            merged_passages = merge_overlapping_passages(passages_for_merge, max_gap=0)

            # Compute score from merged passages
            y = 0.6  # edit similarity weight
            z = 0.4  # pos similarity weight
            score = 0.0
            for mp in merged_passages:
                k = mp.source_end - mp.source_start
                edit_sim = mp.similarity
                pos_sim = mp.pos_similarity
                score += (k / doc_length) * (y * edit_sim + z * pos_sim)

            overall_plagiarism_score = score * 100.0
            overall_plagiarism_score = min(100.0, max(0.0, overall_plagiarism_score))

            reports[doc_id] = [
                doc_id,
                doc_group,
                round(overall_plagiarism_score, 2),
            ]

        return reports

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