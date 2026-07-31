import pytest
import json
from unittest.mock import MagicMock
from app.quiz.quiz_generator import QuizGenerator

@pytest.fixture
def mock_dependencies():
    return {
        "cache": MagicMock(),
        "fact_cache": MagicMock(),
        "llm_client": MagicMock()
    }

def test_generation_reliability_retry_logic(mock_dependencies):
    # Setup generator to fail the first attempt, then succeed
    gen = QuizGenerator(
        cache=mock_dependencies["cache"],
        fact_cache=mock_dependencies["fact_cache"],
        llm_client=mock_dependencies["llm_client"]
    )
    
    # Mock distractor selector to return 3 distractors
    gen.distractor_selector.select_distractors = MagicMock(return_value=["B", "C", "D"])

    # Valid question that passes all validators
    valid_question = {
        "question": "What is Cloud Computing?",
        "options": ["A) Cloud Computing", "B) B", "C) C", "D) D"],
        "correct": "A",
        "correct_text": "Cloud Computing",
        "explanation": "Cloud computing provides computing resources.",
        "supporting_fact": "Cloud computing provides computing resources.",
        "source_note": "test.md",
        "fact_id": "f1",
        "topic": "Cloud",
        "subtopic": "",
        "concept": "Cloud Computing",
        "concept_type": "concept",
        "cognitive_type": "recognition"
    }
    
    valid_parsed_response = {"questions": [valid_question]}

    # Force failure on first call, success on second
    mock_dependencies["llm_client"].generate.side_effect = [
        "INVALID JSON",
        json.dumps(valid_question)
    ]
    
    # Mock parser to return None for first, and valid container for second
    def parse_side_effect(raw):
        print(f"DEBUG: parser.parse called with: {raw}")
        if raw == "INVALID JSON":
            return None
        return valid_parsed_response

    gen.parser.parse = MagicMock(side_effect=parse_side_effect)
    
    # Mock extract_questions to return the parsed question list
    def extract_side_effect(parsed):
        print(f"DEBUG: parser.extract_questions called with: {parsed}")
        if not parsed:
            return []
        return [valid_question]

    gen.parser.extract_questions = MagicMock(side_effect=extract_side_effect)
    
    # Run generation
    question = gen.generate_with_retry(
        fact="Cloud computing provides computing resources.",
        answer="Cloud Computing",
        topic="Cloud"
    )
    
    assert question is not None
    # Find the correct letter for "Cloud Computing"
    correct_letter = question["correct"]
    correct_option = next(opt for opt in question["options"] if opt.startswith(f"{correct_letter})"))
    assert "Cloud Computing" in correct_option
    
    assert mock_dependencies["llm_client"].generate.call_count == 2
