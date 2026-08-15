import pytest
from app.quiz.storage.question_cache import QuestionCache

@pytest.fixture
def cache(tmp_path):
    return QuestionCache(
        cache_file=str(tmp_path / "test_cache.json")
    )

def test_exclude_ids_filtering(cache):
    q1 = {
        "question_id": "id-A",
        "question": "Question A?",
        "options": ["A) First", "B) Second", "C) Third", "D) Fourth"],
        "correct": "A",
        "correct_text": "Correct A",
        "explanation": "Valid explanation for A",
        "supporting_fact": "This is a valid supporting fact for A",
        "source_note": "Note A",
        "fact_id": "fact-A",
        "concept": "Concept A"
    }
    q2 = {
        "question_id": "id-B",
        "question": "Question B?",
        "options": ["A) First", "B) Second", "C) Third", "D) Fourth"],
        "correct": "B",
        "correct_text": "Correct B",
        "explanation": "Valid explanation for B",
        "supporting_fact": "This is a valid supporting fact for B",
        "source_note": "Note B",
        "fact_id": "fact-B",
        "concept": "Concept B"
    }
    q3 = {
        "question_id": "id-C",
        "question": "Question C?",
        "options": ["A) First", "B) Second", "C) Third", "D) Fourth"],
        "correct": "C",
        "correct_text": "Correct C",
        "explanation": "Valid explanation for C",
        "supporting_fact": "This is a valid supporting fact for C",
        "source_note": "Note C",
        "fact_id": "fact-C",
        "concept": "Concept C"
    }
    
    # Missing ID should be handled safely
    q4_no_id = {
        "question": "Question D?",
        "options": ["A) First", "B) Second", "C) Third", "D) Fourth"],
        "correct": "D",
        "correct_text": "Correct D",
        "explanation": "Valid explanation for D",
        "supporting_fact": "This is a valid supporting fact for D",
        "source_note": "Note D",
        "fact_id": "fact-D",
        "concept": "Concept D"
    }

    cache.add_to_pool(
        "AI",
        "",
        "medium",
        "multiple_choice",
        [q1, q2, q3, q4_no_id]
    )

    # Sample without exclusions
    res_no_ex = cache.sample("AI", "", "medium", "multiple_choice", count=10)
    assert len(res_no_ex) == 4

    # Sample with exclude_ids=["id-A"]
    res_ex_a = cache.sample("AI", "", "medium", "multiple_choice", count=10, exclude_ids=["id-A"])
    assert len(res_ex_a) == 3
    ids = [q.get("question_id") for q in res_ex_a]
    assert "id-A" not in ids
    assert "id-B" in ids
    assert "id-C" in ids
