from app.pipeline.stylometry.style_analyzer import StylometryAnalyzer


def test_stylometry_analyzer_empty_text_returns_zero_features():
    analyzer = StylometryAnalyzer()
    result = analyzer.analyze("")

    assert result == {
        "avg_sentence_length": 0.0,
        "std_sentence_length": 0.0,
        "type_token_ratio": 0.0,
        "function_word_ratio": 0.0,
        "punctuation_ratio": 0.0,
    }


def test_stylometry_analyzer_basic_text():
    analyzer = StylometryAnalyzer()
    result = analyzer.analyze("The test is short. This is 1 sentence.")

    assert result["avg_sentence_length"] > 0
    assert 0.0 <= result["type_token_ratio"] <= 1.0
    assert 0.0 <= result["function_word_ratio"] <= 1.0
    assert 0.0 <= result["punctuation_ratio"] <= 1.0
