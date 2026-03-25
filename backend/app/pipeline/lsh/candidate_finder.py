from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Set, Tuple

from datasketch import MinHash, MinHashLSH

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ShingleConfig:
    size: int = 3
    max_shingles: int = 100_000


@dataclass(frozen=True)
class MinHashConfig:
    num_perm: int = 128
    seed: int = 1


@dataclass(frozen=True)
class LSHConfig:
    threshold: float = 0.5
    num_perm: int = 128


class Shingler:
    """Generate k-word shingles from token sequences with limits."""

    def __init__(self, config: ShingleConfig | None = None) -> None:
        self.config = config or ShingleConfig()
        if self.config.size <= 0:
            raise ValueError("Shingle size must be positive")

    def shingles(self, tokens: Sequence[str]) -> Set[str]:
        if not isinstance(tokens, Sequence):
            raise TypeError("tokens must be a sequence")

        k = self.config.size
        if len(tokens) < k:
            return set()

        result: Set[str] = set()
        for i in range(len(tokens) - k + 1):
            if len(result) >= self.config.max_shingles:
                logger.warning(
                    "Shingle limit %d reached; truncating", self.config.max_shingles
                )
                break
            result.add(" ".join(tokens[i : i + k]))
        return result


class CandidateFinder:
    """
    Use MinHash + LSH to find similar document pairs.

    This is intended as a coarse filter before more expensive analysis.
    """

    def __init__(
        self,
        minhash_config: MinHashConfig | None = None,
        lsh_config: LSHConfig | None = None,
    ) -> None:
        self.minhash_config = minhash_config or MinHashConfig()
        self.lsh_config = lsh_config or LSHConfig(
            threshold=0.5, num_perm=self.minhash_config.num_perm
        )

        if self.minhash_config.num_perm != self.lsh_config.num_perm:
            raise ValueError(
                "minhash_config.num_perm must match lsh_config.num_perm"
            )

    def _create_minhash(self, shingles: Iterable[str]) -> MinHash:
        m = MinHash(num_perm=self.minhash_config.num_perm, seed=self.minhash_config.seed)
        for s in shingles:
            m.update(s.encode("utf-8", errors="ignore"))
        return m

    def find_candidates(
        self,
        doc_shingles: Dict[str, Iterable[str]],
    ) -> List[Tuple[str, str, float]]:
        """
        Find candidate document pairs.

        Returns (doc_id_a, doc_id_b, approx_jaccard).
        """
        if not isinstance(doc_shingles, dict):
            raise TypeError("doc_shingles must be a dict of id -> shingles")

        lsh = MinHashLSH(
            threshold=self.lsh_config.threshold,
            num_perm=self.lsh_config.num_perm,
        )

        minhashes: Dict[str, MinHash] = {}

        for doc_id, shingles in doc_shingles.items():
            shingles_list = list(shingles)
            if not shingles_list:
                continue

            mh = self._create_minhash(shingles_list)
            minhashes[doc_id] = mh
            try:
                lsh.insert(doc_id, mh)
            except ValueError:
                # Very unlikely but we guard against LSH internal issues
                logger.exception("Failed to insert doc_id %s into LSH", doc_id)

        seen: Set[Tuple[str, str]] = set()
        candidates: List[Tuple[str, str, float]] = []

        for doc_id, mh in minhashes.items():
            try:
                similar_ids = lsh.query(mh)
            except Exception:
                logger.exception("Failed to query LSH for doc_id %s", doc_id)
                continue

            for other in similar_ids:
                if other == doc_id:
                    continue
                pair = tuple(sorted((doc_id, other)))
                if pair in seen:
                    continue
                seen.add(pair)
                score = mh.jaccard(minhashes[other])
                candidates.append((pair[0], pair[1], float(score)))

        return candidates


__all__ = [
    "ShingleConfig",
    "MinHashConfig",
    "LSHConfig",
    "Shingler",
    "CandidateFinder",
]

