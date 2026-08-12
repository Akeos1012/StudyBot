import pytest
from unittest.mock import MagicMock
from app.services.quiz_service import QuizService

from app.learning.analytics.analytics_repository import AnalyticsRepository
from app.learning.analytics.analytics_service import LearningAnalyticsService

@pytest.fixture
def mock_dependencies():
    metadata_loader = MagicMock()
    quiz_generator = MagicMock()
    pool_manager = MagicMock()
    recommendation_engine = MagicMock()
    quiz_session_service = MagicMock()
    analytics_repository = MagicMock(spec=AnalyticsRepository)
    return metadata_loader, quiz_generator, pool_manager, recommendation_engine, quiz_session_service, analytics_repository

def test_healthy_pool_no_expansion(mock_dependencies):
    metadata_loader, quiz_generator, pool_manager, recommendation_engine, quiz_session_service, analytics_repository = mock_dependencies
    # Mock analytics service
    mock_analytics_service = MagicMock(spec=LearningAnalyticsService)

    service = QuizService(
        metadata_loader,
        quiz_generator,
        pool_manager,
        recommendation_engine,
        quiz_session_service,
        analytics_repository,
        mock_analytics_service,
    )
    
    # Mock healthy pool
    pool_manager.should_expand_pool.return_value = {"expand": False}
    
    # Need to mock cache retrieval within QuizGenerator/Service
    quiz_generator.cache.sample.return_value = [{"question": "q1"}]
    
    # Execution
    service.get_or_generate_questions("Cloud", count=1)
    
    # Verify
    pool_manager.should_expand_pool.assert_called_once()
    assert quiz_generator.cache.sample.called

def test_unhealthy_pool_expansion_triggered(mock_dependencies):
    metadata_loader, quiz_generator, pool_manager, recommendation_engine, quiz_session_service, analytics_repository = mock_dependencies
    # Mock analytics service
    mock_analytics_service = MagicMock(spec=LearningAnalyticsService)

    service = QuizService(
        metadata_loader,
        quiz_generator,
        pool_manager,
        recommendation_engine,
        quiz_session_service,
        analytics_repository,
        mock_analytics_service,
    )
    
    # Mock unhealthy pool
    pool_manager.should_expand_pool.return_value = {"expand": True}
    
    # Mock cache retrieval
    quiz_generator.cache.sample.return_value = [{"question": "q1"}]
    
    # Execution
    service.get_or_generate_questions("Cloud", count=1)
    
    # Verify
    pool_manager.should_expand_pool.assert_called_once()
    pool_manager.expand_pool.assert_called_once()
    assert quiz_generator.cache.sample.called

def test_record_answer_normalizes_labeled_input():
    # Setup
    mock_analytics_service = MagicMock(spec=LearningAnalyticsService)
    mock_repo = MagicMock(spec=AnalyticsRepository)
    quiz_generator = MagicMock()
    cache = MagicMock()
    quiz_generator.cache = cache
    
    service = QuizService(
        metadata_loader=MagicMock(),
        quiz_generator=quiz_generator,
        pool_manager=MagicMock(),
        recommendation_engine=MagicMock(),
        quiz_session_service=MagicMock(),
        analytics_repository=mock_repo,
        analytics_service=mock_analytics_service
    )
    
    question = {
        "question": "Q?",
        "options": ["A) A", "B) B"],
        "correct": "A",
        "concept": "C1",
        "metadata": {"success_rate": 0.5}
    }
    cache.get_question_by_id.return_value = question
    
    # Act
    # Frontend sends labeled answer
    result = service.record_answer("q1", "A) A")
    
    # Assert
    assert result["correct"] is True

def test_record_answer_normalizes_raw_input():
    # Setup
    mock_analytics_service = MagicMock(spec=LearningAnalyticsService)
    mock_repo = MagicMock(spec=AnalyticsRepository)
    quiz_generator = MagicMock()
    cache = MagicMock()
    quiz_generator.cache = cache
    
    service = QuizService(
        metadata_loader=MagicMock(),
        quiz_generator=quiz_generator,
        pool_manager=MagicMock(),
        recommendation_engine=MagicMock(),
        quiz_session_service=MagicMock(),
        analytics_repository=mock_repo,
        analytics_service=mock_analytics_service
    )
    
    question = {
        "question": "Q?",
        "options": ["A) A", "B) B"],
        "correct": "A",
        "concept": "C1",
        "metadata": {"success_rate": 0.5}
    }
    cache.get_question_by_id.return_value = question
    
    # Act
    # Frontend sends raw text answer
    result = service.record_answer("q1", "A")
    
    # Assert
    assert result["correct"] is True

