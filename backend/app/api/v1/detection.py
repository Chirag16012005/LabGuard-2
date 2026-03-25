from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

from .documents import Document
from ...pipeline.preprocessing.text_normalizer import TextNormalizer
from ...pipeline.preprocessing.sentence_splitter import SentenceSplitter
from ...pipeline.preprocessing.tokenizer import Tokenizer
from ...pipeline.lsh.candidate_finder import (
    CandidateFinder,
    LSHConfig,
    MinHashConfig,
    ShingleConfig,
    Shingler,
)
from ...pipeline.gst.greedy_string_tiling import GreedyStringTiler
from ...pipeline.merging.passage_merger import PassageMatch, merge_overlapping_passages

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

    def detect(self, documents: Iterable[Document]) -> Dict[str, Dict]:
        """
        Run the full plagiarism detection pipeline.

        Returns mapping of document_id -> report.
        """
        docs_list = list(documents)
        if len(docs_list) < 2:
            return {}

        doc_map: Dict[str, Document] = {d.id: d for d in docs_list}

        shingles_by_doc = self._build_shingles(docs_list)
        candidates = self.candidate_finder.find_candidates(shingles_by_doc)

        if not candidates:
            return {doc.id: self._empty_report(doc.id) for doc in docs_list}

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
                start_char = self._approx_char_offset(tokens_a, tile.src_start)
                end_char = self._approx_char_offset(tokens_a, tile.src_end)

                seg_a = norm_a[start_char:end_char]
                seg_b = norm_b[
                    self._approx_char_offset(tokens_b, tile.dst_start) : self._approx_char_offset(
                        tokens_b, tile.dst_end
                    )
                ]
                raw_sim = self._raw_text_similarity(seg_a, seg_b)
                if raw_sim < self.config.raw_similarity_threshold:
                    continue

                # Placeholder POS/stylometry checks; assume structural similarity for now.
                pos_sim = 1.0
                if pos_sim < self.config.pos_similarity_threshold:
                    continue

                all_passages.append(
                    PassageMatch(
                        source_doc_id=doc_a,
                        target_doc_id=doc_b,
                        start_pos=start_char,
                        end_pos=end_char,
                        similarity=float(raw_sim),
                    )
                )

        merged = merge_overlapping_passages(all_passages, max_gap=5)
        return self._build_reports(doc_map, merged)

    @staticmethod
    def _approx_char_offset(tokens: List[str], token_index: int) -> int:
        """Approximate character offset in a space-joined string."""
        if token_index <= 0:
            return 0
        if token_index > len(tokens):
            token_index = len(tokens)
        return sum(len(t) + 1 for t in tokens[:token_index])

    @staticmethod
    def _levenshtein_distance(a: str, b: str) -> int:
        if a == b:
            return 0
        if not a:
            return len(b)
        if not b:
            return len(a)
        if len(a) < len(b):
            a, b = b, a

        previous = list(range(len(b) + 1))
        for i, ca in enumerate(a, start=1):
            current = [i]
            for j, cb in enumerate(b, start=1):
                ins = previous[j] + 1
                dele = current[j - 1] + 1
                sub = previous[j - 1] + (ca != cb)
                current.append(min(ins, dele, sub))
            previous = current
        return previous[-1]

    def _raw_text_similarity(self, a: str, b: str) -> float:
        if not a and not b:
            return 0.0
        dist = self._levenshtein_distance(a, b)
        max_len = max(len(a), len(b))
        return 1.0 - (dist / max_len)

    @staticmethod
    def _empty_report(doc_id: str) -> Dict:
        return {"document_id": doc_id, "plagiarism_score": 0.0, "matched_passages": []}

    def _build_reports(
        self,
        docs: Dict[str, Document],
        passages: Iterable[PassageMatch],
    ) -> Dict[str, Dict]:
        """Aggregate passages into per-document reports."""
        reports: Dict[str, Dict] = {
            doc_id: self._empty_report(doc_id) for doc_id in docs.keys()
        }

        for p in passages:
            src_report = reports[p.source_doc_id]
            src_report.setdefault("matched_passages", []).append(
                {
                    "source_doc": p.target_doc_id,
                    "start_pos": p.start_pos,
                    "end_pos": p.end_pos,
                    "similarity": p.similarity,
                }
            )

        for doc_id, report in reports.items():
            doc = docs[doc_id]
            total_len = max(len(doc.content), 1)
            plag_chars = 0
            for mp in report.get("matched_passages", []):
                plag_chars += max(0, mp["end_pos"] - mp["start_pos"])
            score = (plag_chars / total_len) * 100.0
            report["plagiarism_score"] = round(score, 2)

        return reports


__all__ = ["PlagiarismConfig", "PlagiarismDetector"]

