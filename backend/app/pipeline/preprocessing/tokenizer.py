from __future__ import annotations

import logging
import re
from typing import List

logger = logging.getLogger(__name__)


class Tokenizer:
    """Heuristic word tokenizer with limits."""

    DEFAULT_MAX_TOKENS = 200_000

    _TOKEN_RE = re.compile(r"[^\w]+", flags=re.UNICODE)

    def __init__(self, max_tokens: int | None = None) -> None:
        self.max_tokens = max_tokens or self.DEFAULT_MAX_TOKENS

    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize (normalized) text into tokens.

        For production accuracy, replace with an NLP tokenizer such as spaCy.
        """
        if text is None:
            raise ValueError("text must not be None")

        if not isinstance(text, str):
            raise TypeError(f"text must be str, got {type(text).__name__}")

        stripped = text.strip()
        if not stripped:
            return []

        tokens = [t for t in self._TOKEN_RE.split(stripped) if t]
        if len(tokens) > self.max_tokens:
            logger.warning(
                "Token count %d exceeds max_tokens=%d; truncating",
                len(tokens),
                self.max_tokens,
            )
            tokens = tokens[: self.max_tokens]
        return tokens


__all__ = ["Tokenizer"]

