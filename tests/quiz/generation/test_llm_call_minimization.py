import pytest
from unittest.mock import MagicMock
from app.quiz.generation.quiz_generator import QuizGenerator
from app.quiz.generation.llm_client import LLMClient

def test_llm_not_called_for_invalid_fact():
    # Mock LLM client
    mock_llm = MagicMock(spec=LLMClient)
    
    # Initialize QuizGenerator with the mocked LLM
    gen = QuizGenerator(llm_client=mock_llm)
    
    # Define an invalid fact
    invalid_fact = {"concept": "X", "supporting_fact": "not grounded"}
    
    # Try to generate
    gen.generate_questions(topic="Test", count=1, supporting_facts=[invalid_fact])
    
    # Verify LLM was NOT called
    mock_llm.generate.assert_not_called()

def test_llm_called_for_valid_fact():
    # Mock LLM client
    mock_llm = MagicMock(spec=LLMClient)
    # Mock LLM response to simulate success
    mock_llm.generate.return_value = '{"questions": [{"question": "What is X?", "options": ["A) X", "B) Y", "C) Z", "D) W"], "correct": "A", "explanation": "X is Y"}]}'
    
    # Initialize QuizGenerator with the mocked LLM
    gen = QuizGenerator(llm_client=mock_llm)
    
    # Define a valid fact
    valid_fact = {"concept": "Deep Learning", "supporting_fact": "Deep Learning is AI"}
    
    # Try to generate
    gen.generate_questions(topic="Test", count=1, supporting_facts=[valid_fact])
    
    # Verify LLM WAS called
    assert mock_llm.generate.call_count > 0
