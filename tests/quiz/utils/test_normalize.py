import pytest
from app.quiz.utils.question_similarity import normalize

def test_normalize_word_boundaries():
    # Should not corrupt words
    assert normalize("artificially") == "artificially"
    assert normalize("existing") == "existing"
    assert normalize("training") == "training"

    # Should remove stop/question words
    assert normalize("what is a test") == "test"
    assert normalize("which of these are correct") == "correct"
    assert normalize("does this work") == "work"
    assert normalize("an apple") == "apple"
    assert normalize("the technique") == "technique"

    # Complex case
    assert normalize("Which technique is used to artificially expand existing data?") == "technique used to artificially expand existing data?"
