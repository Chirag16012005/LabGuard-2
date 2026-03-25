from __future__ import annotations

import logging
import re
from typing import List

logger = logging.getLogger(__name__)


class SentenceSplitter:
    """Heuristic sentence splitter with basic safeguards."""

    DEFAULT_MAX_SENTENCES = 10_000

    _SENTENCE_BOUNDARY_RE = re.compile(r"([.!?])\s+")

    def __init__(self, max_sentences: int | None = None) -> None:
        self.max_sentences = max_sentences or self.DEFAULT_MAX_SENTENCES

    def split(self, text: str) -> List[str]:
        """
        Split (normalized) text into sentences.

        For better accuracy in production, replace with an NLP library
        such as spaCy's sentence segmentation.
        """
        if text is None:
            raise ValueError("text must not be None")

        if not isinstance(text, str):
            raise TypeError(f"text must be str, got {type(text).__name__}")

        stripped = text.strip()
        if not stripped:
            return []

        if not any(p in stripped for p in (".", "!", "?")):
            return [stripped]

        parts: List[str] = []
        start = 0
        for match in self._SENTENCE_BOUNDARY_RE.finditer(stripped):
            end = match.end()
            sentence = stripped[start:end].strip()
            if sentence:
                parts.append(sentence)
                if len(parts) >= self.max_sentences:
                    logger.warning(
                        "Sentence count exceeded max_sentences=%d; truncating",
                        self.max_sentences,
                    )
                    return parts
            start = end

        if start < len(stripped):
            remainder = stripped[start:].strip()
            if remainder:
                parts.append(remainder)

        return parts


__all__ = ["SentenceSplitter"]

