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

        For identical texts, returns 1.0.
        For completely different texts of same length, returns 0.0.
        Handles empty strings gracefully.

        Args:
            a: First text.
            b: Second text.

        Returns:
            Similarity score between 0.0 and 1.0.
            - 1.0: texts are identical
            - 0.0: texts are completely different
        """
        # Both empty → structurally identical
        if not a and not b:
            return 1.0

        # One empty, one not → completely different
        if not a or not b:
            return 0.0

        # Identical texts
        if a == b:
            return 1.0

        # Compute normalized Levenshtein distance
        dist = self.levenshtein_distance(a, b)
        max_len = max(len(a), len(b))

        # Avoid division by zero (shouldn't happen since we checked for empty)
        if max_len == 0:
            return 1.0

        # Normalize: 0 edits = 1.0 similarity, max_len edits ≈ 0.0 similarity
        similarity = 1.0 - (dist / max_len)

        # Clamp to [0, 1]
        return max(0.0, min(1.0, similarity))
