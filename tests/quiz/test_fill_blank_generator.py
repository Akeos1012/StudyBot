import pytest
from app.quiz.generation.fill_blank_generator import FillBlankGenerator

@pytest.fixture
def generator():
    return FillBlankGenerator()

def test_clean_question_text_removes_extra_blanks(generator):
    text = "This is a _______ test _______ with two blanks."
    cleaned = generator._clean_question_text(text)
    
    assert cleaned.count("_______") == 1
    assert "test" in cleaned
    assert "with" in cleaned

def test_clean_question_text_fixes_formatting(generator):
    text = "_______ is It is created during the Training process. An is a trained system."
    cleaned = generator._clean_question_text(text)
    
    assert cleaned.count("_______") == 1
    assert cleaned.endswith(".")

def test_trivial_definition_rejected(generator):
    assert generator._is_trivial_fill_blank("_______ is a programming technique.") is True
    assert generator._is_trivial_fill_blank("_______ are used for data.") is True
    assert generator._is_trivial_fill_blank("_______ was developed for performance.") is True
    assert generator._is_trivial_fill_blank("_______ were designed efficiently.") is True

def test_contextual_fill_blank_accepted(generator):
    assert generator._is_trivial_fill_blank("By using _______, we can improve performance.") is False
    assert generator._is_trivial_fill_blank("The algorithm uses _______ to reduce computation.") is False
    assert generator._is_trivial_fill_blank("A system can use _______ to process large data.") is False
    assert generator._is_trivial_fill_blank("_______.") is False  # Too short to match pattern anyway
