import pytest
from unittest.mock import MagicMock

from app.services.quiz_service import QuizService
from app.quiz.quiz_generator import QuizGenerator
from app.quiz.question_cache import QuestionCache
from app.rag.fact_cache import FactCache
from app.quiz.llm_client import LLMClient
from app.rag.metadata_loader import MetadataLoader


@pytest.fixture
def test_fact_cache():
    cache = FactCache()

    cache.cache = {
        "Cloud": [
            {
                "id": "fact_001",
                "topic": "Cloud",
                "concept": "Object Storage",
                "supporting_fact": "Object storage stores data as objects."
            },
            {
                "id": "fact_002",
                "topic": "Cloud",
                "concept": "File Storage",
                "supporting_fact": "File storage stores files in a hierarchical structure."
            },
            {
                "id": "fact_003",
                "topic": "Cloud",
                "concept": "Block Storage",
                "supporting_fact": "Block storage divides data into fixed-size blocks."
            },
            {
                "id": "fact_004",
                "topic": "Cloud",
                "concept": "Database Storage",
                "supporting_fact": "Database storage organizes structured information."
            }
        ]
    }

    return cache


@pytest.fixture
def mock_llm_client():
    client = MagicMock(spec=LLMClient)

    client.generate.return_value = """
    {
        "questions": [
            {
                "question": "What type of storage stores data as objects?",
                "options": [
                    "A) Object storage",
                    "B) File storage",
                    "C) Block storage",
                    "D) Database storage"
                ],
                "correct": "A",
                "correct_text": "Object storage",
                "explanation": "Object storage stores information as objects with unique identifiers.",
                "supporting_fact": "Object storage stores data as objects.",
                "type": "multiple_choice"
            }
        ]
    }
    """

    return client

@pytest.fixture
def metadata_loader(tmp_path):

    notes_dir = tmp_path / "notes"
    cloud_dir = notes_dir / "Cloud"

    cloud_dir.mkdir(parents=True)

    note_file = cloud_dir / "storage.md"

    note_file.write_text(
        """
    # Cloud

    ## Object Storage

    Object storage is a cloud storage method that stores data as objects.

    ## Characteristics

    Object storage uses unique identifiers to organize and retrieve data.
    It is commonly used for scalable cloud storage systems.
        """,
        encoding="utf-8"
    )

    return MetadataLoader(
        str(notes_dir)
    )

@pytest.fixture
def quiz_service(
    test_fact_cache,
    mock_llm_client,
    metadata_loader,
    tmp_path
):

    question_cache = QuestionCache(cache_file=str(tmp_path / "question_cache.json"))

    generator = QuizGenerator(
        cache=question_cache, fact_cache=test_fact_cache, llm_client=mock_llm_client
    )

    return QuizService(
        metadata_loader=metadata_loader,
        quiz_generator=generator
    )


def test_full_pipeline_orchestration(quiz_service):

    result = quiz_service.generate_questions_for_topic(
        topic="Cloud",
        subtopic=None,
        count=1
    )
    print(result)

    assert len(result) == 1
    assert "question" in result[0]

def test_quiz_generator_direct(
    test_fact_cache,
    mock_llm_client,
    tmp_path
):

    question_cache = QuestionCache(
        cache_file=str(tmp_path / "question_cache.json")
    )

    generator = QuizGenerator(
        cache=question_cache,
        fact_cache=test_fact_cache,
        llm_client=mock_llm_client
    )

    facts = test_fact_cache.cache["Cloud"]

    print("\nFACTS:")
    print(facts)

    questions = generator.generate_questions(
        topic="Cloud",
        supporting_facts=facts,
        count=1
    )

    print("\nGENERATED:")
    print(questions)

    assert len(questions) == 1