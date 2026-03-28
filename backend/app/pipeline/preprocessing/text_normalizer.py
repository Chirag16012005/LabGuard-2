from __future__ import annotations

import logging
import re
import unicodedata
from typing import Iterable, List

logger = logging.getLogger(__name__)


class TextNormalizer:
    """Robust text normalization for plagiarism detection."""

    DEFAULT_MAX_LENGTH = 500_000  # characters

    _PUNCTUATION_MAP = {
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "–": "-",
        "—": "-",
        "…": "...",
    }

    _WHITESPACE_RE = re.compile(r"\s+")

    def __init__(self, max_length: int | None = None) -> None:
        self.max_length = max_length or self.DEFAULT_MAX_LENGTH

    def normalize(self, text: str) -> str:
        """
        Normalize input text.

        - Validates input type and length
        - Applies Unicode NFKC normalization
        - Lowercases
        - Normalizes common punctuation variants
        - Collapses whitespace
        """
        if text is None:
            raise ValueError("text must not be None")

        if not isinstance(text, str):
            raise TypeError(f"text must be str, got {type(text).__name__}")

        if not text.strip():
            return ""

        if len(text) > self.max_length:
            logger.warning(
                "Input text length %d exceeds max_length=%d; truncating",
                len(text),
                self.max_length,
            )
            text = text[: self.max_length]

        text = unicodedata.normalize("NFKC", text)
        text = text.lower()

        for src, dst in self._PUNCTUATION_MAP.items():
            text = text.replace(src, dst)

        text = self._WHITESPACE_RE.sub(" ", text).strip()
        return text

    def normalize_many(self, texts: Iterable[str]) -> List[str]:
        """Normalize an iterable of texts, skipping and logging failures."""
        normalized: List[str] = []
        for idx, t in enumerate(texts):
            try:
                normalized.append(self.normalize(t))
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception("Failed to normalize text at index %d: %s", idx, exc)
        return normalized


__all__ = ["TextNormalizer"]

