from __future__ import annotations

import math
from typing import Dict, List

from ..preprocessing.sentence_splitter import SentenceSplitter
from ..preprocessing.tokenizer import Tokenizer


class StylometryAnalyzer:
    """Analyze writing style features for a document."""

    FUNCTION_WORDS = {"the", "is", "in", "at", "of", "and", "to", "a"}

    def __init__(self) -> None:
        self.splitter = SentenceSplitter()
        self.tokenizer = Tokenizer()

    def analyze(self, text: str) -> Dict[str, float]:
        """Compute stylometry features for provided text."""
        if text is None:
            raise ValueError("text must not be None")

        normalized = text.strip()
        if not normalized:
            return {
                "avg_sentence_length": 0.0,
                "std_sentence_length": 0.0,
                "type_token_ratio": 0.0,
                "function_word_ratio": 0.0,
                "punctuation_ratio": 0.0,
            }

        # ✅ Tokenize once (optimization)
        tokens = self.tokenizer.tokenize(normalized)

        # Sentence-level analysis
        sentences: List[str] = self.splitter.split(normalized)
        sentence_lengths: List[int] = []

        for sentence in sentences:
            words = self.tokenizer.tokenize(sentence)
            if words:  # avoid empty sentences
                sentence_lengths.append(len(words))

        # Sentence statistics
        if sentence_lengths:
            avg_sentence_length = sum(sentence_lengths) / len(sentence_lengths)
            variance = sum(
                (length - avg_sentence_length) ** 2 for length in sentence_lengths
            ) / len(sentence_lengths)
            std_sentence_length = math.sqrt(variance)
        else:
            avg_sentence_length = 0.0
            std_sentence_length = 0.0

        # Word-level features
        total_words = len(tokens)

        unique_words = len(set(w.lower() for w in tokens))
        type_token_ratio = (unique_words / total_words) if total_words > 0 else 0.0

        function_word_count = sum(
            1 for w in tokens if w.lower() in self.FUNCTION_WORDS
        )
        function_word_ratio = (
            function_word_count / total_words if total_words > 0 else 0.0
        )

        # Punctuation usage
        punctuation_chars = sum(
            1 for ch in normalized if ch in ".,!?:;()[]{}-\"'`"
        )
        punctuation_ratio = (
            punctuation_chars / len(normalized) if normalized else 0.0
        )

        return {
            "avg_sentence_length": float(avg_sentence_length),
            "std_sentence_length": float(std_sentence_length),
            "type_token_ratio": float(type_token_ratio),
            "function_word_ratio": float(function_word_ratio),
            "punctuation_ratio": float(punctuation_ratio),
        }


__all__ = ["StylometryAnalyzer"]
