from __future__ import annotations

from typing import List

from ..similarity.edit_distance import EditDistance
from .pos_tagger import POSTagger


class POSSimilarity:
    """
    Computes POS-based similarity between texts.
    """

    def __init__(self, tagger: POSTagger) -> None:
        """
        Initialize with a POS tagger.

        Args:
            tagger: POSTagger instance.
        """
        self.tagger = tagger
        self.edit_distance = EditDistance()
        self._pos_cache = {}
        
    def _get_pos(self, text: str):
        if text in self._pos_cache:
            return self._pos_cache[text]

        tags = self.tagger.tag(text)
        self._pos_cache[text] = tags
        return tags

    def similarity(self, a: str, b: str) -> float:
        """
        Compute POS-based similarity between two texts.

        This compares grammatical structure (POS tags) to detect paraphrasing,
        even in short sequences. Does not reject short sequences outright.

        Args:
            a: First text.
            b: Second text.

        Returns:
            Similarity score between 0.0 and 1.0.
        """
        if not isinstance(a, str) or not isinstance(b, str):
            raise TypeError("Both arguments must be strings")

        pos_a = self._get_pos(a)
        pos_b = self._get_pos(b)

        # Both empty → consider structurally identical (neutral)
        if not pos_a and not pos_b:
            return 1.0

        # One empty, one not → structural mismatch
        if not pos_a or not pos_b:
            return 0.0

        # For very short sequences (< 2 tokens), return neutral score
        # A 1-token sequence has no internal structure to compare
        if len(pos_a) == 1 and len(pos_b) == 1:
            # Both single tokens → they match if they're the same POS tag
            return 1.0 if pos_a[0] == pos_b[0] else 0.0

        # Sequences of 2+ tokens: compare via edit distance
        distance = self.edit_distance.levenshtein_distance(pos_a, pos_b)
        max_len = max(len(pos_a), len(pos_b))
        similarity = 1.0 - (distance / max_len)

        # Clamp to [0, 1]
        return max(0.0, min(1.0, similarity))
