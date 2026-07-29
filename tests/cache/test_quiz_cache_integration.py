import pytest

from app.rag.fact_cache import FactCache
from app.quiz.quiz_generator import QuizGenerator


@pytest.fixture
def mock_fact_cache():
    cache = FactCache()

    cache.facts = [
        {
            "fact_id": "fact_001",
            "topic": "Cloud Computing",
            "content": "Object storage stores data as objects."
        }
    ]

    return cache


@pytest.fixture
def quiz_generator(mock_fact_cache):
    return QuizGenerator(
        fact_cache=mock_fact_cache
    )


def test_quiz_generation_uses_cache(
    quiz_generator
):
    result = quiz_generator.generate_questions(
        topic="Cloud Computing",
        count=1
    )

    assert result is not None
    assert isinstance(result, dict)