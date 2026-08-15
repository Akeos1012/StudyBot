import pytest
from app.quiz.generation.question_scorer import QuestionScorer

@pytest.fixture
def scorer():
    return QuestionScorer()

def test_score_answer_exposure(scorer):
    # Case: Exact restatement
    q1 = {"question": "What is Block Storage?", "correct_text": "Block Storage"}
    score1 = scorer._score_answer_exposure(q1)
    assert score1 == 0.0 # ExposureLevel.HIGH.value

    # Case: Natural context
    q2 = {"question": "Which scenario uses Block Storage?", "correct_text": "Block Storage"}
    score2 = scorer._score_answer_exposure(q2)
    assert score2 == 1.0 # ExposureLevel.LOW.value

def test_score_cognitive_validity(scorer):
    # Case: Missing cognitive type (pass)
    q1 = {"question": "What is Block Storage?"}
    score1 = scorer._score_cognitive_validity(q1)
    assert score1 == 1.0

    # Case: Classification missing keyword (penalty)
    q2 = {"question": "Block Storage is...", "cognitive_type": "classification"}
    score2 = scorer._score_cognitive_validity(q2)
    assert score2 == 0.5
