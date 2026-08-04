import pytest
from app.models.smart_reviewer_schema import SmartReviewerResult

def test_valid_smart_reviewer_result():
    """Test creating a valid SmartReviewerResult."""
    data = {
        "question_id": "q123",
        "user_answer": "A",
        "correct_answer": "B",
        "is_correct": False,
        "explanation": "Explanation here.",
        "supporting_fact": "Fact here.",
        "source_note": "note1.md",
        "fact_id": "f123",
        "related_concepts": ["Concept X"]
    }
    result = SmartReviewerResult(**data)
    
    assert result.question_id == "q123"
    assert result.is_correct is False
    assert len(result.related_concepts) == 1
    assert result.related_concepts[0] == "Concept X"

def test_missing_required_fields():
    """Test that missing required fields raises a validation error."""
    data = {
        "question_id": "q123"
        # missing other required fields
    }
    with pytest.raises(ValueError):
        SmartReviewerResult(**data)

def test_empty_related_concepts():
    """Confirm related_concepts can be empty."""
    data = {
        "question_id": "q123",
        "user_answer": "A",
        "correct_answer": "A",
        "is_correct": True,
        "explanation": "Good.",
        "supporting_fact": "Fact.",
        "source_note": "note1.md",
        "fact_id": "f123"
    }
    result = SmartReviewerResult(**data)
    assert result.related_concepts == []

def test_serialization():
    """Confirm model serializes correctly."""
    data = {
        "question_id": "q123",
        "user_answer": "A",
        "correct_answer": "B",
        "is_correct": False,
        "explanation": "Explanation here.",
        "supporting_fact": "Fact here.",
        "source_note": "note1.md",
        "fact_id": "f123"
    }
    result = SmartReviewerResult(**data)
    serialized = result.model_dump()
    
    assert serialized["question_id"] == "q123"
    assert "related_concepts" in serialized
    assert serialized["related_concepts"] == []
