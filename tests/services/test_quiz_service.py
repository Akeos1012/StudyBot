import pytest
from unittest.mock import MagicMock
from app.services.quiz_service import QuizService

@pytest.fixture
def mock_dependencies():
    metadata_loader = MagicMock()
    quiz_generator = MagicMock()
    pool_manager = MagicMock()
    return metadata_loader, quiz_generator, pool_manager

def test_healthy_pool_no_expansion(mock_dependencies):
    metadata_loader, quiz_generator, pool_manager = mock_dependencies
    service = QuizService(metadata_loader, quiz_generator, pool_manager)
    
    # Mock healthy pool
    pool_manager.should_expand_pool.return_value = {"expand": False}
    
    # Need to mock cache retrieval within QuizGenerator/Service
    quiz_generator.cache.sample.return_value = [{"question": "q1"}]
    
    # Execution
    service.get_or_generate_questions("Cloud", count=1)
    
    # Verify
    pool_manager.should_expand_pool.assert_called_once()
    pool_manager.expand_pool.assert_not_called()
    assert quiz_generator.cache.sample.called

def test_unhealthy_pool_expansion_triggered(mock_dependencies):
    metadata_loader, quiz_generator, pool_manager = mock_dependencies
    service = QuizService(metadata_loader, quiz_generator, pool_manager)
    
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

def test_pool_manager_failure_fallback(mock_dependencies):
    metadata_loader, quiz_generator, pool_manager = mock_dependencies
    service = QuizService(metadata_loader, quiz_generator, pool_manager)
    
    # Mock failure
    pool_manager.should_expand_pool.side_effect = Exception("Service unavailable")
    
    # Mock existing fallback generation (must be able to generate)
    quiz_generator.cache.sample.return_value = []
    
    # Execution (should not crash)
    try:
        service.get_or_generate_questions("Cloud", count=1)
    except Exception as e:
        pytest.fail(f"QuizService crashed on PoolManager failure: {e}")
