import pytest
from unittest.mock import MagicMock, patch
from app.quiz.generation.quiz_generator import QuizGenerator
from app.quiz.generation.llm_client import LLMClient
from app.quiz.generation.retry_policy import FailureType

@pytest.fixture
def mock_llm():
    return MagicMock(spec=LLMClient)

@pytest.fixture
def gen(mock_llm):
    return QuizGenerator(llm_client=mock_llm)

def test_test_matrix(gen, mock_llm):
    # Scenario: Invalid fact (Priority #3)
    # Expected: 0 LLM calls
    mock_llm.generate.reset_mock()
    invalid_fact = {"concept": "", "supporting_fact": ""}
    gen.generate_questions(topic="Test", count=1, supporting_facts=[invalid_fact])
    assert mock_llm.generate.call_count == 0

    # Scenario: Valid fact + deterministic grounding failure (Priority #4)
    # Expected: 1 LLM call
    mock_llm.generate.reset_mock()
    # Mock LLM to return valid JSON but the validators will reject it
    # We force the parser to return a question that grounding validation will reject
    # In generate_from_fact, it parses content -> extract_questions -> question[0] -> validation
    
    # Let's mock the validator to return False for grounding
    valid_fact = {"concept": "Deep Learning", "supporting_fact": "Deep Learning is AI"}
    
    with patch("app.quiz.generation.quiz_generator.validate_grounding", return_value=False), \
         patch("app.quiz.generation.quiz_generator.DistractorSelector.select_distractors", return_value=["D1", "D2", "D3"]):
        mock_llm.generate.return_value = '{"questions": [{"question": "What is DL?", "options": ["A) DL", "B) B", "C) C", "D) D"], "correct": "A"}]}'
        gen.generate_questions(topic="Test", count=1, supporting_facts=[valid_fact])
        assert mock_llm.generate.call_count == 1
    # Scenario: Valid fact + malformed JSON (Priority #4)
    # Expected: 3 LLM calls
    mock_llm.generate.reset_mock()
    mock_llm.generate.return_value = 'invalid json'
    gen.generate_questions(topic="Test", count=1, supporting_facts=[valid_fact])
    assert mock_llm.generate.call_count == 3
