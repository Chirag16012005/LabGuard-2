from __future__ import annotations

from typing import Sequence, TypeVar

T = TypeVar('T')


class EditDistance:
    """
    Computes edit distance between sequences using dynamic programming.
    """

    def levenshtein_distance(self, a: Sequence[T], b: Sequence[T]) -> int:
        """
        Compute Levenshtein distance between two sequences.

        Args:
            a: First sequence.
            b: Second sequence.

        Returns:
            Edit distance.
        """
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

    def raw_text_similarity(self, a: str, b: str) -> float:
        """
        Compute raw text similarity using Levenshtein distance.

        Args:
            a: First text.
            b: Second text.

        Returns:
            Similarity score between 0.0 and 1.0.
        """
        if not a and not b:
            return 0.0
        dist = self.levenshtein_distance(a, b)
        max_len = max(len(a), len(b))
        return 1.0 - (dist / max_len)
