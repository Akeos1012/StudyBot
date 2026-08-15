import pytest
from unittest.mock import MagicMock
from app.quiz.generation.quiz_generator import QuizGenerator
from app.quiz.generation.retry_policy import FailureType

# Mock LLM and validation to simulate deterministic failures
class MockQuizGenerator(QuizGenerator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.llm.generate = MagicMock()

def test_deterministic_failure_not_retried():
    # Setup
    mock_llm = MagicMock()
    # Simulate a deterministic validation error (e.g., grounding)
    # The generator calls generate_from_fact, which returns None, error
    
    # We'll need to mock generate_from_fact on the QuizGenerator instance
    gen = QuizGenerator(llm_client=mock_llm)
    gen.generate_from_fact = MagicMock(return_value=(None, "Grounding validation failed"))
    
    fact = "Deterministic grounding failure fact"
    answer = "Concept"
    
    # Attempt generation
    gen.generate_with_retry(
        fact=fact,
        answer=answer,
        topic="Test",
        max_attempts=3
    )
    
    # Assert LLM was called only once for the fact
    # In generate_with_retry, the first attempt is attempt=0
    # generate_from_fact is called inside the loop
    # If it fails deterministically, it should not loop
    assert gen.generate_from_fact.call_count == 1
    
    # Verify LLMClient.generate was not called at all (since fact failed grounding)
    assert mock_llm.generate.call_count == 0

def test_retryable_failure_is_retried():
    # Setup
    mock_llm = MagicMock()
    gen = QuizGenerator(llm_client=mock_llm)
    
    # Simulate a retryable error (e.g., JSON parsing)
    gen.generate_from_fact = MagicMock(return_value=(None, "JSON parsing failed"))
    
    fact = "Retryable failure fact"
    answer = "Concept"
    
    # Attempt generation
    gen.generate_with_retry(
        fact=fact,
        answer=answer,
        topic="Test",
        max_attempts=3
    )
    
    # Assert generate_from_fact was called 3 times
    assert gen.generate_from_fact.call_count == 3
