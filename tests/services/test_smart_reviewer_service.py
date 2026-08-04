import pytest
from unittest.mock import MagicMock
from app.services.smart_reviewer_service import SmartReviewerService
from app.rag.fact_cache import FactCache

@pytest.fixture
def mock_fact_cache():
    cache = MagicMock(spec=FactCache)
    # Default behavior for most tests
    cache.get_facts.return_value = [
        {"concept": "Concept A", "definition": "A"},
        {"concept": "Concept B", "definition": "B"},
        {"concept": "Cloud Storage", "definition": "C"}
    ]
    return cache

@pytest.fixture
def service(mock_fact_cache):
    return SmartReviewerService(mock_fact_cache)

@pytest.fixture
def sample_question():
    return {
        "question_id": "q1",
        "fact_id": "f1",
        "supporting_fact": "Fact about cloud",
        "source_note": "note1.md",
        "explanation": "Exp",
        "correct": "A",
        "concept": "Cloud Storage",
        "topic": "Cloud"
    }

def test_generate_review_incorrect_answer(service, sample_question):
    result = service.generate_review(sample_question, "B")
    assert result.is_correct is False
    assert result.correct_answer == "A"
    assert result.explanation == "Exp"
    # Traceability check
    assert result.question_id == sample_question["question_id"]
    assert result.fact_id == sample_question["fact_id"]
    assert result.supporting_fact == sample_question["supporting_fact"]
    assert result.source_note == sample_question["source_note"]

def test_generate_review_correct_answer(service, sample_question):
    result = service.generate_review(sample_question, "A")
    assert result.is_correct is True
    assert result.correct_answer == "A"
    assert result.explanation == "Exp"
    # Traceability check
    assert result.question_id == sample_question["question_id"]
    assert result.fact_id == sample_question["fact_id"]
    assert result.supporting_fact == sample_question["supporting_fact"]
    assert result.source_note == sample_question["source_note"]

def test_missing_metadata(service, sample_question):
    del sample_question["fact_id"]
    with pytest.raises(ValueError, match="Question missing required field"):
        service.generate_review(sample_question, "A")

# Related concepts tests
def test_related_concepts_same_topic_returned(service, mock_fact_cache):
    mock_fact_cache.get_facts.return_value = [
        {"concept": "Concept A", "definition": "A"},
        {"concept": "Concept B", "definition": "B"},
        {"concept": "Cloud Storage", "definition": "C"}
    ]
    question = {"topic": "Cloud", "concept": "Cloud Storage"}
    result = service._get_related_concepts(question)
    assert "Concept A" in result
    assert "Concept B" in result

def test_related_concepts_excludes_current_concept(service, mock_fact_cache):
    mock_fact_cache.get_facts.return_value = [
        {"concept": "Concept A", "definition": "A"},
        {"concept": "Cloud Storage", "definition": "C"}
    ]
    question = {"topic": "Cloud", "concept": "Cloud Storage"}
    result = service._get_related_concepts(question)
    assert "Cloud Storage" not in result
    assert "Concept A" in result

def test_related_concepts_no_cross_topic_pollution(service, mock_fact_cache):
    # Verify the service queries the FactCache with the correct topic
    question = {"topic": "Database", "concept": "SQL"}
    service._get_related_concepts(question)
    mock_fact_cache.get_facts.assert_called_with("Database")

def test_related_concepts_limit(service, mock_fact_cache):
    mock_fact_cache.get_facts.return_value = [
        {"concept": "C1", "definition": "1"},
        {"concept": "C2", "definition": "2"},
        {"concept": "C3", "definition": "3"},
        {"concept": "C4", "definition": "4"},
        {"concept": "C5", "definition": "5"},
        {"concept": "C6", "definition": "6"}
    ]
    question = {"topic": "Cloud", "concept": "Ignore"}
    result = service._get_related_concepts(question)
    assert len(result) == 5

def test_related_concepts_missing_metadata_safe(service, mock_fact_cache):
    # Missing topic
    assert service._get_related_concepts({}) == []
    # Missing concept - should return others
    mock_fact_cache.get_facts.return_value = [{"concept": "A", "definition": "1"}]
    assert service._get_related_concepts({"topic": "Cloud"}) == ["A"]

def test_missing_source_note_returns_null(service, sample_question):
    # Remove optional fields
    del sample_question["source_note"]
    del sample_question["supporting_fact"]
    
    result = service.generate_review(sample_question, "A")
    
    # Should not raise exception
    assert result.question_id == "q1"
    assert result.source_note is None
    assert result.supporting_fact is None
