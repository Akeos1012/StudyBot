import pytest
from unittest.mock import MagicMock
from app.quiz.pool_manager import PoolManager
from app.monitoring.pool_metrics import PoolMetrics

@pytest.fixture
def mock_dependencies():
    cache = MagicMock()
    generator = MagicMock()
    retriever = MagicMock()
    pool_metrics = MagicMock(spec=PoolMetrics)
    return cache, generator, retriever, pool_metrics

def test_dynamic_target_calculation(mock_dependencies):
    cache, generator, retriever, pool_metrics = mock_dependencies
    manager = PoolManager(cache, generator, retriever, pool_metrics)
    
    # Small topic
    retriever.retrieve.return_value = ["fact1"]
    target = manager.calculate_target_pool_size("Small")
    assert target["target_size"] == 5 # min_pool_size floor
    
    # Large topic
    retriever.retrieve.return_value = ["f"] * 100
    target = manager.calculate_target_pool_size("Large")
    assert target["target_size"] == 50

def test_distribution_analysis(mock_dependencies):
    cache, generator, retriever, pool_metrics = mock_dependencies
    manager = PoolManager(cache, generator, retriever, pool_metrics)
    
    # Mocking sample to return a mix of difficulty and types
    cache.sample.return_value = [
        {"difficulty": "easy", "type": "multiple_choice"},
        {"difficulty": "medium", "type": "multiple_choice"}
    ]
    cache.get_pool_size.return_value = 2
    
    dist = manager.analyze_distribution("Cloud")
    assert dist["total"] == 2
    assert dist["difficulty"]["easy"] == 1
    assert dist["types"]["multiple_choice"] == 2

def test_missing_question_calculation(mock_dependencies):
    cache, generator, retriever, pool_metrics = mock_dependencies
    manager = PoolManager(cache, generator, retriever, pool_metrics)
    
    # Mock target = 10 (20 facts * 0.5), pool = 2
    retriever.retrieve.return_value = ["f"] * 20
    cache.get_pool_size.return_value = 2
    
    # Mock distribution analysis to show 2 MC
    cache.sample.return_value = [{"type": "multiple_choice"}, {"type": "multiple_choice"}]
    
    missing = manager.calculate_missing_questions("Cloud")
    assert missing["total_missing"] > 0

def test_should_expand_pool(mock_dependencies):
    cache, generator, retriever, pool_metrics = mock_dependencies
    manager = PoolManager(cache, generator, retriever, pool_metrics)
    
    # Below target (Total pool will be 0)
    retriever.retrieve.return_value = ["f"] * 20
    cache.get_pool_size.return_value = 0
    decision = manager.should_expand_pool("Cloud")
    assert decision["expand"] is True

    # Balanced
    cache.get_pool_size.return_value = 50 # Total pool will be 300
    decision = manager.should_expand_pool("Cloud")
    # Need to ensure distribution analysis doesn't force expansion
    assert decision["expand"] is False

def test_expand_pool_metrics(mock_dependencies):
    cache, generator, retriever, pool_metrics = mock_dependencies
    manager = PoolManager(cache, generator, retriever, pool_metrics)
    
    # Setup for expansion needed
    retriever.retrieve.return_value = ["f"] * 20
    cache.get_pool_size.return_value = 0
    cache.sample.return_value = [] # Balanced distribution to avoid imbalance trigger
    generator.generate_questions.return_value = {"questions": [{"q": "new"}]}
    
    # Execute
    success = manager.expand_pool("Cloud")
    
    # Verify
    assert success is True
    assert generator.generate_questions.called
    assert cache.add_to_pool.called
    pool_metrics.record_expansion_attempt.assert_called_once()
    pool_metrics.record_expansion_success.assert_called_once()

def test_expand_pool_failure_metrics(mock_dependencies):
    cache, generator, retriever, pool_metrics = mock_dependencies
    manager = PoolManager(cache, generator, retriever, pool_metrics)
    
    # Setup for expansion failure
    retriever.retrieve.return_value = ["f"] * 20
    cache.get_pool_size.return_value = 0
    generator.generate_questions.side_effect = Exception("Generation failed")
    
    # Execute
    success = manager.expand_pool("Cloud")
    
    # Verify
    assert success is False
    pool_metrics.record_expansion_attempt.assert_called_once()
    pool_metrics.record_expansion_failure.assert_called_once()
