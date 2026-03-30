from __future__ import annotations

import spacy
from typing import List


class POSTagger:
    """
    POS tagger using spaCy for grammatical structure analysis.
    """

    def __init__(self, model: str = "en_core_web_sm") -> None:
        """
        Initialize the POS tagger with a spaCy model.

        Args:
            model: Name of the spaCy model to load.
        """
        try:
            self.nlp = spacy.load(model)
        except OSError:
            raise RuntimeError(
                f"spaCy model '{model}' not found. "
                f"Please install it with: python -m spacy download {model}"
            )

    def tag(self, text: str) -> List[str]:
        """
        Tokenize text and return POS tags.

        Args:
            text: Input text to tag.

        Returns:
            List of POS tags (e.g., ["DET", "NOUN", "VERB", "NOUN"]).
        """
        if not text.strip():
            return []

        doc = self.nlp(text, disable=["parser", "ner"])
        return [token.pos_ for token in doc]
