import pytest
from unittest.mock import MagicMock
from app.services.quiz_service import QuizService

from app.learning.analytics.analytics_repository import AnalyticsRepository

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
    service = QuizService(metadata_loader, quiz_generator, pool_manager, recommendation_engine, quiz_session_service, analytics_repository)
    
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
    service = QuizService(metadata_loader, quiz_generator, pool_manager, recommendation_engine, quiz_session_service, analytics_repository)
    
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

