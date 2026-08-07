import pytest
import json
from unittest.mock import MagicMock, patch
from app.quiz.generation.quiz_generator import QuizGenerator
from app.monitoring.metrics_context import MetricsContext
from app.monitoring.quiz_metrics import QuizMetrics
from app.quiz.validation.question_validator import is_valid_question

# ... (keep existing imports and fixture)

@pytest.fixture
def mock_dependencies():
    return {
        "cache": MagicMock(),
        "fact_cache": MagicMock(),
        "llm_client": MagicMock()
    }

def test_instrumentation_validation_failures(mock_dependencies):
    gen = QuizGenerator(
        cache=mock_dependencies["cache"],
        fact_cache=mock_dependencies["fact_cache"],
        llm_client=mock_dependencies["llm_client"]
    )
    
    # Mock LLM and parser to return a question
    question = {
        "question": "What is Cloud Computing?",
        "options": ["A) A", "B) B", "C) C", "D) D"],
        "correct": "A",
        "type": "multiple_choice",
        "concept": "Cloud Computing"
    }
    
    mock_dependencies["llm_client"].generate.return_value = json.dumps({"questions": [question]})
    gen.parser.parse = MagicMock(return_value={"questions": [question]})
    gen.parser.extract_questions = MagicMock(return_value=[question])
    
    metrics = QuizMetrics(topic="Cloud")
    context = MetricsContext(quiz_metrics=metrics, topic="Cloud")
    
    # Patch validate_semantic to fail
    with patch("app.quiz.generation.quiz_generator.validate_semantic", return_value=False):
        # We need to mock other validators to ensure they pass
        with patch("app.quiz.generation.quiz_generator.validate_structure", return_value=True), \
             patch("app.quiz.generation.quiz_generator.validate_distractors", return_value=True), \
             patch("app.quiz.generation.quiz_generator.validate_domain_correctness", return_value=True), \
             patch("app.quiz.generation.quiz_generator.is_relevant_to_topic", return_value=True):
            
            gen.generate_questions(
                topic="Cloud",
                count=1,
                supporting_facts=[{"concept": "Cloud Computing", "definition": "Fact Fact Fact", "topic": "Cloud", "source": "test.md"}],

                metrics_context=context
            )
    assert metrics.validation_failures.get("semantic") >= 1

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

def test_retry_exhaustion_records_failure(mock_dependencies):
    gen = QuizGenerator(
        cache=mock_dependencies["cache"],
        fact_cache=mock_dependencies["fact_cache"],
        llm_client=mock_dependencies["llm_client"]
    )
    
    # Always return invalid response
    mock_dependencies["llm_client"].generate.return_value = "INVALID"
    gen.parser.parse = MagicMock(return_value=None)
    
    metrics = QuizMetrics(topic="Cloud")
    context = MetricsContext(quiz_metrics=metrics, topic="Cloud")
    
    question = gen.generate_with_retry(
        fact="Fact",
        answer="Answer",
        topic="Cloud",
        metrics_context=context
    )
    
    assert question is None
    assert metrics.failed_after_max_retries == 1

def test_empty_supporting_facts_handled_safely(mock_dependencies):
    gen = QuizGenerator(
        cache=mock_dependencies["cache"],
        fact_cache=mock_dependencies["fact_cache"],
        llm_client=mock_dependencies["llm_client"]
    )
    
    # Using the public interface generate_questions
    # Pass empty supporting_facts
    result = gen.generate_questions(
        topic="Cloud",
        supporting_facts=[]
    )
    
    # The current contract returns a dict when empty, not a list
    assert isinstance(result, dict)
    assert "questions" in result
    assert len(result["questions"]) == 0

def test_invalid_json_exhausts_retries(mock_dependencies):
    gen = QuizGenerator(
        cache=mock_dependencies["cache"],
        fact_cache=mock_dependencies["fact_cache"],
        llm_client=mock_dependencies["llm_client"]
    )
    
    # Always return malformed JSON
    mock_dependencies["llm_client"].generate.return_value = "{malformed: json}"
    gen.parser.parse = MagicMock(return_value=None)
    
    metrics = QuizMetrics(topic="Cloud")
    context = MetricsContext(quiz_metrics=metrics, topic="Cloud")
    
    question = gen.generate_with_retry(
        fact="Fact",
        answer="Answer",
        topic="Cloud",
        metrics_context=context
    )
    
    assert question is None
    assert metrics.failed_after_max_retries == 1

def test_grounding_failure_triggers_retry(mock_dependencies):
    gen = QuizGenerator(
        cache=mock_dependencies["cache"],
        fact_cache=mock_dependencies["fact_cache"],
        llm_client=mock_dependencies["llm_client"]
    )
    
    # Valid struct, but ungrounded answer (concept not in question)
    invalid_question = {
        "question": "What is something else?",
        "options": ["A) Wrong", "B) B", "C) C", "D) D"],
        "correct": "A",
        "explanation": "Unrelated explanation.",
        "supporting_fact": "Fact about X.",
        "source_note": "test.md",
        "fact_id": "f1",
        "topic": "Cloud"
    }
    
    mock_dependencies["llm_client"].generate.side_effect = [
        json.dumps({"questions": [invalid_question]}),
        json.dumps({"questions": [invalid_question]}) # Simplified for demonstration
    ]
    gen.parser.parse = MagicMock(return_value={"questions": [invalid_question]})
    gen.parser.extract_questions = MagicMock(return_value=[invalid_question])
    
    # Should trigger validation failure and retry
    question = gen.generate_with_retry(
        fact="Fact about X.",
        answer="X",
        topic="Cloud",
        max_attempts=2
    )
    
    # With 2 attempts, should return None if invalid
    assert question is None
