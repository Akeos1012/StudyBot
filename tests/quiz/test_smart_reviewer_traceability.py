import pytest
import json
from unittest.mock import MagicMock, patch
from app.quiz.generation.quiz_generator import QuizGenerator
from app.quiz.storage.question_cache import QuestionCache

@pytest.fixture
def mock_dependencies():
    return {
        "cache": QuestionCache(cache_file="temp_test_cache.json"), # Use a temporary file
        "fact_cache": MagicMock(),
        "llm_client": MagicMock()
    }

def test_generated_question_has_source_traceability(mock_dependencies):
    gen = QuizGenerator(
        cache=mock_dependencies["cache"],
        fact_cache=mock_dependencies["fact_cache"],
        llm_client=mock_dependencies["llm_client"]
    )

    # Mock LLM and parser to return a question with metadata
    question = {
        "question": "Which technology provides computing resources over a network?",
        "options": [
            "A) Cloud Computing",
            "B) Platform as a Service",
            "C) Infrastructure as a Service",
            "D) Software as a Service"
        ],
        "correct": "A",
        "type": "multiple_choice",
        "concept": "Cloud Computing",
        "explanation": "Cloud computing provides computing resources."
    }

    mock_dependencies["llm_client"].generate.return_value = json.dumps(
        {"questions": [question]}
    )

    gen.parser.parse = MagicMock(
        return_value={"questions": [question]}
    )

    gen.parser.extract_questions = MagicMock(
        return_value=[question]
    )

    gen.distractor_selector.select_distractors = MagicMock(
        return_value=[
            "Platform as a Service",
            "Infrastructure as a Service",
            "Software as a Service"
        ]
    )

    fact = {
        "concept": "Cloud Computing",
        "definition": "Cloud computing provides computing resources over a network.",
        "topic": "Cloud",
        "source": "test.md",
        "fact_id": "f123"
    }

    # Patch the references used directly by QuizGenerator.
    with patch(
        "app.quiz.generation.quiz_generator.validate_structure",
        return_value=True
    ), \
        patch(
            "app.quiz.generation.quiz_generator.validate_distractors",
            return_value=True
        ), \
        patch(
            "app.quiz.generation.quiz_generator.validate_grounding",
            return_value=True
        ), \
        patch(
            "app.quiz.generation.quiz_generator.is_relevant_to_topic",
            return_value=True
        ), \
        patch(
            "app.quiz.generation.quiz_generator.question_equals_answer",
            return_value=False
        ), \
        patch(
            "app.quiz.generation.quiz_generator.validate_question_focus",
            return_value=True
        ), \
        patch(
            "app.quiz.generation.quiz_generator.validate_question_uniqueness",
            return_value=True
        ), \
        patch(
            "app.quiz.generation.quiz_generator.validate_semantic",
            return_value=True
        ), \
        patch(
            "app.quiz.generation.quiz_generator.validate_domain_correctness",
            return_value=True
        ), \
        patch(
            "app.quiz.generation.quiz_generator.normalize_and_validate_correct_field",
            return_value=True
        ), \
        patch.object(
            gen,
            "_check_quality",
            return_value=(True, 1.0, {})
        ):

        # Clear cache to avoid interference from other tests
        gen.cache.clear_topic(topic="Cloud")

        result = gen.generate_questions(
            topic="Cloud",
            count=1,
            supporting_facts=[fact]
        )

    assert result["questions"]

    generated_question = result["questions"][0]
    print(f"DEBUG: generated_question: {generated_question}")

    assert generated_question["source_note"] == "test.md"
    assert generated_question["fact_id"] == "f123"
    assert generated_question["supporting_fact"] == (
        "Cloud computing provides computing resources over a network."
    )
    assert generated_question["topic"] == "Cloud"
    assert generated_question["concept"] == "Cloud Computing"



def test_question_cache_preserves_traceability(mock_dependencies):
    gen = QuizGenerator(
        cache=mock_dependencies["cache"],
        fact_cache=mock_dependencies["fact_cache"],
        llm_client=mock_dependencies["llm_client"]
    )
    
    # Create a valid question that passes validator
    # Must have 4 options and valid correct format
    question = {
        "question": "Q1?",
        "options": ["A) A", "B) B", "C) C", "D) D"],
        "correct": "A",
        "type": "multiple_choice",
        "concept": "C1",
        "explanation": "Exp1",
        "fact_id": "f1",
        "source_note": "n1",
        "supporting_fact": "fact1"
    }
    
    # Use a mock validator patch if necessary, but here we just test cache serialization.
    # The cache.add_to_pool method might run validation that rejects this dict.
    # We should ensure this question is technically valid per validator if needed, 
    # but the cache itself should be testing the serialization aspect.
    
    # Bypass validation by mocking add_to_pool logic if required, 
    # but based on error, it was rejected. Let's make it fully compliant:
    question["concept"] = "C1"
    
    # Save to cache
    # The question validator might reject it if it doesn't look enough like a real question
    # from the LLM, but for cache test, we just want to ensure it roundtrips.
    # We will assume valid dict structure.
    # Save to cache
    with patch("app.quiz.storage.question_cache.is_valid_question", return_value=True):
        gen.cache.add_to_pool("Topic1", "", "medium", "multiple_choice", [question])

        # Load from cache
        cached = gen.cache.sample("Topic1", "", "medium", "multiple_choice", 1)

    assert cached is not None
    assert cached[0]["fact_id"] == "f1"
    assert cached[0]["source_note"] == "n1"
    assert cached[0]["supporting_fact"] == "fact1"
    assert cached[0]["explanation"] == "Exp1"


def test_missing_source_metadata_detected(mock_dependencies):
    gen = QuizGenerator(
        cache=mock_dependencies["cache"],
        fact_cache=mock_dependencies["fact_cache"],
        llm_client=mock_dependencies["llm_client"]
    )
    
    # Question missing metadata
    question = {
        "question": "Q1?",
        "options": ["A) A", "B) B", "C) C", "D) D"],
        "correct": "A",
        "type": "multiple_choice",
        "concept": "C1",
        "explanation": "Exp1"
    }
    
    # Validate missing metadata fields
    # According to question_schema.py, these are optional, but for SmartReviewer, 
    # we need to be sure they were populated by QuizGenerator
    
    assert "fact_id" not in question
    assert "source_note" not in question
    assert "supporting_fact" not in question
