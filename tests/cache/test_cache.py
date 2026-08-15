import pytest

from app.quiz.storage.question_cache import QuestionCache


@pytest.fixture
def cache(tmp_path):
    return QuestionCache(
        cache_file=str(tmp_path / "test_cache.json")
    )


def test_add_to_pool(cache):
    question = {
        "question": "Which type of cloud storage organizes data as individual objects?",
        "options": [
            "A) Object storage",
            "B) File storage",
            "C) Block storage",
            "D) Network storage",
        ],
        "correct": "A",
        "correct_text": "Object storage",
        "supporting_fact": "Object storage stores data as objects.",
        "explanation": "Object storage is correct because it stores data as objects.",
        "source_note": "cloud_notes.md",
        "fact_id": "fact_001",
    }

    cache.add_to_pool(
        "Cloud Computing",
        "Storage",
        "medium",
        "multiple_choice",
        [question],
    )

    assert cache.get_pool_size(
        "Cloud Computing",
        "Storage",
        "medium",
        "multiple_choice",
    ) == 1


def test_get_pool(cache):
    question = {
        "question": "What stores data as objects?",
        "options": [
            "A) Object storage",
            "B) File storage",
            "C) Block storage",
            "D) Network storage",
        ],
        "correct": "A",
        "correct_text": "Object storage",
        "supporting_fact": "Objects store data.",
        "explanation": "Object storage uses objects.",
        "source_note": "cloud_notes.md",
        "fact_id": "fact_002",
    }

    cache.add_to_pool(
        "Cloud Computing",
        "Storage",
        "medium",
        "multiple_choice",
        [question],
    )

    pool = cache.get_pool(
        "Cloud Computing",
        "Storage",
        "medium",
        "multiple_choice",
    )

    assert len(pool) == 1
    assert pool[0]["fact_id"] == "fact_002"
