import pytest
from unittest.mock import MagicMock
from app.services.quiz_service import QuizService
from app.learning.analytics.analytics_repository import AnalyticsRepository
from app.learning.analytics.analytics_service import LearningAnalyticsService as NewLearningAnalyticsService
from app.learning.recommendation.recommendation_engine import RecommendationEngine


@pytest.fixture
def mock_cache():
    return MagicMock()


@pytest.fixture
def service(mock_cache):
    mock_new_service = MagicMock(spec=NewLearningAnalyticsService)
    mock_repository = MagicMock(spec=AnalyticsRepository)

    return QuizService(
        metadata_loader=MagicMock(),
        quiz_generator=MagicMock(cache=mock_cache),
        pool_manager=MagicMock(),
        recommendation_engine=MagicMock(spec=RecommendationEngine),
        quiz_session_service=MagicMock(),
        analytics_repository=mock_repository,
        analytics_service=mock_new_service,
    )

def test_personalization_disabled(service, mock_cache):
    service.get_or_generate_questions(
        topic="test",
        personalize=False
    )

    mock_cache.sample.assert_called_with(
        "test",
        "",
        "medium",
        "multiple",
        3,
        concept_weights=None,
        exclude_ids=None,
    )


def test_weak_concept_weighting(service, mock_cache):
    service.analytics_service.get_weak_topics.return_value = [
        {
            "topic": "recursion",
            "mastery": 0.2,
            "priority": "high",
        }
    ]

    service.recommendation_engine.get_concept_weights.return_value = {
        "recursion": 2
    }

    mock_cache.sample.return_value = [
        {"question_id": "q1"},
        {"question_id": "q2"},
        {"question_id": "q3"},
    ]

    service.get_or_generate_questions(
        topic="test",
        personalize=True,
        user_context=MagicMock(user_id="u1"),
    )

    service.analytics_service.get_weak_topics.assert_called_once_with("u1")

    service.recommendation_engine.get_concept_weights.assert_called_once_with(
        ["recursion"],
        [],
    )

    mock_cache.sample.assert_called_with(
        "test",
        "",
        "medium",
        "multiple",
        3,
        concept_weights={"recursion": 2},
        exclude_ids=None,
    )


def test_no_user_history(service, mock_cache):
    service.analytics_service.get_weak_topics.return_value = []

    service.recommendation_engine.get_concept_weights.return_value = {}

    mock_cache.sample.return_value = [
        {"question_id": "q1"},
        {"question_id": "q2"},
        {"question_id": "q3"},
    ]

    service.get_or_generate_questions(
        topic="test",
        personalize=True,
        user_context=MagicMock(user_id="u1"),
    )

    service.analytics_service.get_weak_topics.assert_called_once_with("u1")

    service.recommendation_engine.get_concept_weights.assert_called_once_with(
        [],
        [],
    )

    mock_cache.sample.assert_called_with(
        "test",
        "",
        "medium",
        "multiple",
        3,
        concept_weights={},
        exclude_ids=None,
    )


def test_fallback_logic(service, mock_cache):
    mock_cache.sample.return_value = None

    service.analytics_service.get_weak_topics.return_value = []

    generated_questions = [
        {
            "question_id": "q1",
            "question": "Generated question",
            "concept": "Cloud Storage",
            "metadata": {"success_rate": 0.0},
        }
    ]

    service.generate_questions_for_topic = MagicMock(
        return_value=generated_questions
    )

    result = service.get_or_generate_questions(
        topic="test",
        personalize=True,
        user_context=MagicMock(user_id="u1"),
    )

    service.analytics_service.get_weak_topics.assert_called_once_with("u1")

    service.generate_questions_for_topic.assert_called_once()

    assert result == generated_questions