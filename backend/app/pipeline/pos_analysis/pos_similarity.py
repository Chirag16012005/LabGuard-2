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

        Args:
            a: First text.
            b: Second text.

        Returns:
            Similarity score between 0.0 and 1.0.
        """
        pos_a = self._get_pos(a)
        pos_b = self._get_pos(b)

        if not pos_a and not pos_b:
            return 1.0  # Both empty, consider identical
        if not pos_a or not pos_b:
            return 0.0  # One empty, no similarity
        
        if len(pos_a) < 3 or len(pos_b) < 3:
            return 0.0

        # Compute edit distance between POS sequences
        distance = self.edit_distance.levenshtein_distance(pos_a, pos_b)
        max_len = max(len(pos_a), len(pos_b))
        similarity = 1.0 - (distance / max_len)

        return max(0.0, min(1.0, similarity))  # Clamp to [0, 1]
