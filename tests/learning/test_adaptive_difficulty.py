import pytest
from unittest.mock import MagicMock
from app.services.quiz_service import QuizService
from app.models.user_context import UserContext
from app.learning.analytics.analytics_repository import AnalyticsRepository
from app.learning.analytics.analytics_service import LearningAnalyticsService
from app.learning.recommendation.recommendation_engine import RecommendationEngine

@pytest.fixture
def mock_quiz_service():
    mock_meta = MagicMock()
    mock_gen = MagicMock()
    mock_pool = MagicMock()
    mock_recommendation = MagicMock(spec=RecommendationEngine)
    mock_session = MagicMock()
    mock_repository = MagicMock(spec=AnalyticsRepository)
    mock_analytics_service = MagicMock(spec=LearningAnalyticsService)
    
    return QuizService(
        mock_meta, mock_gen, mock_pool, mock_recommendation, mock_session, mock_repository, mock_analytics_service
    ), mock_repository

def test_adaptive_disabled(mock_quiz_service):
    service, mock_repository = mock_quiz_service
    user_context = UserContext(user_id="user1")
    
    # Adaptive disabled, should NOT call repository
    service.get_or_generate_questions(
        topic="Database",
        difficulty="hard",
        user_context=user_context,
        adaptive=False
    )
    
    mock_repository.get_mastery_records.assert_not_called()

def test_adaptive_enabled_with_mastery(mock_quiz_service):
    service, mock_repository = mock_quiz_service
    user_context = UserContext(user_id="user1")
    
    # Mock mastery recommendation data
    mock_repository.get_mastery_records.return_value = [{"mastery_score": 0.2}] # 0.2 score usually maps to easy/medium
    
    # Adaptive enabled, should override difficulty
    service.get_or_generate_questions(
        topic="Database",
        difficulty="hard",
        user_context=user_context,
        adaptive=True
    )
    
    mock_repository.get_mastery_records.assert_called_with(user_context.user_id)

def test_adaptive_enabled_new_user(mock_quiz_service):
    service, mock_repository = mock_quiz_service
    user_context = UserContext(user_id="new_user")
    
    # Mock no mastery
    mock_repository.get_mastery_records.return_value = []
    
    service.get_or_generate_questions(
        topic="Database",
        difficulty="hard",
        user_context=user_context,
        adaptive=True
    )
    
    # Should call, but get None, so difficulty "hard" remains
    mock_repository.get_mastery_records.assert_called_once()
