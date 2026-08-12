
import pytest
from app.quiz.generation.question_scorer import QuestionScorer

@pytest.fixture
def scorer():
    return QuestionScorer()

def test_trivial_definition_copying_penalized(scorer):
    # Definition-copying question
    question = {
        "question": "What is Data Augmentation?",
        "options": ["A) Data Augmentation", "B) Linear Growth", "C) Constant Time", "D) Quadratic Time"],
        "correct": "A",
        "explanation": "Data Augmentation is a technique."
    }
    
    # We expect a penalty (semantic score < 0.9)
    # The new logic for trivial definition-copying should make the first component 0.5
    
    # Mocking explanation_supported_by_fact to return True
    import app.quiz.validation.question_grounding
    from unittest.mock import patch
    with patch('app.quiz.validation.question_grounding.explanation_supported_by_fact', return_value=True):
        score = scorer._score_semantic(question)
    
    # Components: 0.5 (Triviality penalty), 1.0 (Correct text match), 1.0 (Explanation)
    # Average: 2.5 / 3 = 0.833...
    assert score < 0.9
    assert score > 0.8

def test_conceptual_question_accepted(scorer):
    # Contextual/conceptual question
    question = {
        "question": "Which technique artificially expands training data to reduce overfitting?",
        "options": ["A) Data Augmentation", "B) Backpropagation", "C) Deep Learning", "D) Regularization"],
        "correct": "A",
        "explanation": "Data Augmentation is a technique."
    }
    
    import app.quiz.validation.question_grounding
    from unittest.mock import patch
    with patch('app.quiz.validation.question_grounding.explanation_supported_by_fact', return_value=True):
        score = scorer._score_semantic(question)
    
    # Components: 0.9 (No triviality), 1.0 (Correct text match), 1.0 (Explanation)
    # Average: 2.9 / 3 = 0.966...
    assert score >= 0.9
