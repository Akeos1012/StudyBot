import pytest
from app.quiz.generation.quiz_generator import QuizGenerator
from app.quiz.validation.fact_validator import FactValidator
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_validator():
    return MagicMock(spec=FactValidator)

def test_fact_prevalidation_integration():
    # Setup
    mock_llm = MagicMock()
    # Define a valid fact and an invalid fact
    valid_fact = {"concept": "Deep Learning", "supporting_fact": "Deep Learning is AI", "fact_id": "f1"}
    invalid_fact = {"concept": "X", "supporting_fact": "not grounded", "fact_id": "f2"}
    
    # Initialize QuizGenerator
    gen = QuizGenerator(llm_client=mock_llm)
    
    # Mock the FactValidator
    # Validator returns False for invalid_fact
    def validate_side_effect(fact):
        if fact["fact_id"] == "f2":
            return MagicMock(valid=False, reason="grounding_failure")
        return MagicMock(valid=True)
    
    gen.fact_validator.validate = MagicMock(side_effect=validate_side_effect)
    
    # Mock generate_from_fact to verify LLM call count
    gen.generate_from_fact = MagicMock(return_value=({"question": "Q", "options": ["A) A", "B) B", "C) C", "D) D"], "correct": "A"}, None))
    
    # Attempt generation
    gen.generate_questions(topic="Test", count=2, supporting_facts=[valid_fact, invalid_fact])
    
    # Assert LLM was called only once (for valid_fact)
    assert gen.generate_from_fact.call_count == 1
