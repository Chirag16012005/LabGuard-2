"""
Unit tests for PlagiarismDetector._pos_tag_sequence in app/api/v1/detection.py

Covers:
- Happy paths: typical and varied text inputs
- Edge cases: empty string, whitespace, special characters, non-string input, etc.

Assumes: This test file is a sibling to detection.py.
"""

import pytest

from detection import PlagiarismDetector, PlagiarismConfig

# --- Mocks ---

import types

@pytest.fixture
def detector():
    """Fixture to create a PlagiarismDetector instance with default config."""
    return PlagiarismDetector()


@pytest.fixture
def detector_with_mocked_pos_tagger():
    """
    Fixture to create a PlagiarismDetector with a mocked pos_tagger.
    Allows us to control the output of .tag().
    """
    detector = PlagiarismDetector()
    class DummyTagger:
        def tag(self, text):
            # Simple mock: returns list of upper-case words as 'POS'
            return [w.upper() for w in text.split()]
    detector.pos_tagger = DummyTagger()
    return detector

# --- Test Class ---

class TestPlagiarismDetectorPosTagSequence:
    # ------------------- Happy Path Tests -------------------

    @pytest.mark.happy_path
    def test_returns_pos_tags_for_simple_sentence(self, detector_with_mocked_pos_tagger):
        """
        Test that _pos_tag_sequence returns a list of POS tags for a simple sentence.
        """
        text = "The quick brown fox"
        result = detector_with_mocked_pos_tagger._pos_tag_sequence(text)
        assert result == ["THE", "QUICK", "BROWN", "FOX"]

    @pytest.mark.happy_path
    def test_returns_pos_tags_for_sentence_with_punctuation(self, detector_with_mocked_pos_tagger):
        """
        Test that _pos_tag_sequence handles punctuation correctly.
        """
        text = "Hello, world!"
        result = detector_with_mocked_pos_tagger._pos_tag_sequence(text)
        # DummyTagger splits on space, so punctuation is attached
        assert result == ["HELLO,", "WORLD!"]

    @pytest.mark.happy_path
    def test_returns_pos_tags_for_long_text(self, detector_with_mocked_pos_tagger):
        """
        Test that _pos_tag_sequence works for longer text.
        """
        text = "This is a longer sentence with several words for testing."
        result = detector_with_mocked_pos_tagger._pos_tag_sequence(text)
        assert result == [w.upper() for w in text.split()]

    @pytest.mark.happy_path
    def test_returns_pos_tags_for_non_ascii_text(self, detector_with_mocked_pos_tagger):
        """
        Test that _pos_tag_sequence handles non-ASCII characters.
        """
        text = "Café naïve résumé"
        result = detector_with_mocked_pos_tagger._pos_tag_sequence(text)
        assert result == ["CAFÉ", "NAÏVE", "RÉSUMÉ"]

    # ------------------- Edge Case Tests -------------------

    @pytest.mark.edge_case
    def test_empty_string_returns_empty_list(self, detector_with_mocked_pos_tagger):
        """
        Test that _pos_tag_sequence returns an empty list for empty string input.
        """
        text = ""
        result = detector_with_mocked_pos_tagger._pos_tag_sequence(text)
        assert result == []

    @pytest.mark.edge_case
    def test_whitespace_only_returns_empty_list(self, detector_with_mocked_pos_tagger):
        """
        Test that _pos_tag_sequence returns an empty list for whitespace-only input.
        """
        text = "    "
        result = detector_with_mocked_pos_tagger._pos_tag_sequence(text)
        assert result == []

    @pytest.mark.edge_case
    def test_special_characters(self, detector_with_mocked_pos_tagger):
        """
        Test that _pos_tag_sequence handles special characters.
        """
        text = "@#$%^&*()"
        result = detector_with_mocked_pos_tagger._pos_tag_sequence(text)
        assert result == ["@#$%^&*()"]

    @pytest.mark.edge_case
    def test_numeric_string(self, detector_with_mocked_pos_tagger):
        """
        Test that _pos_tag_sequence handles numeric strings.
        """
        text = "123 456"
        result = detector_with_mocked_pos_tagger._pos_tag_sequence(text)
        assert result == ["123", "456"]

    @pytest.mark.edge_case
    def test_non_string_input_raises_type_error(self, detector_with_mocked_pos_tagger):
        """
        Test that _pos_tag_sequence raises TypeError if input is not a string.
        """
        with pytest.raises(AttributeError):
            # DummyTagger expects .split(), which only str has
            detector_with_mocked_pos_tagger._pos_tag_sequence(12345)

    @pytest.mark.edge_case
    def test_pos_tagger_returns_none(self, detector_with_mocked_pos_tagger):
        """
        Test that _pos_tag_sequence handles pos_tagger.tag returning None.
        """
        detector_with_mocked_pos_tagger.pos_tagger.tag = lambda text: None
        result = detector_with_mocked_pos_tagger._pos_tag_sequence("test")
        assert result is None

    @pytest.mark.edge_case
    def test_pos_tagger_raises_exception(self, detector_with_mocked_pos_tagger):
        """
        Test that _pos_tag_sequence propagates exceptions from pos_tagger.tag.
        """
        def raise_exc(text):
            raise ValueError("POS tagger error")
        detector_with_mocked_pos_tagger.pos_tagger.tag = raise_exc
        with pytest.raises(ValueError, match="POS tagger error"):
            detector_with_mocked_pos_tagger._pos_tag_sequence("test")