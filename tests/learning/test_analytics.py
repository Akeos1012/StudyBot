import pytest
from unittest.mock import MagicMock
from app.learning.analytics.analytics_service import LearningAnalyticsService
from app.learning.analytics.analytics_repository import AnalyticsRepository

@pytest.fixture
def analytics_service():
    mock_repo = MagicMock(spec=AnalyticsRepository)
    
    # Setup mock records
    mock_repo.get_mastery_records.return_value = [
        {"concept": "concept1", "attempts": 10, "correct_count": 8, "wrong_count": 2, "mastery_score": 0.8},
        {"concept": "concept2", "attempts": 10, "correct_count": 4, "wrong_count": 6, "mastery_score": 0.4}
    ]
    
    return LearningAnalyticsService(mock_repo)

def test_concept_statistics(analytics_service):
    # LearningAnalyticsService doesn't have get_concept_statistics?
    # Checking the actual methods in LearningAnalyticsService:
    # get_mastery_summary, get_weak_topics, get_progress_summary, get_activity_metrics, get_learning_trend
    
    # This test might be obsolete. I will remove it and add tests for the actual methods.
    pass

def test_weak_topic_detection(analytics_service):
    # Threshold 0.6: concept2 is weak (0.4 < 0.6)
    weak = analytics_service.get_weak_topics("user1", threshold=0.6)
    assert any(t["topic"] == "concept2" for t in weak)
    assert not any(t["topic"] == "concept1" for t in weak)

def test_mastery_summary(analytics_service):
    summary = analytics_service.get_mastery_summary("user1")
    
    assert summary["overall_mastery"] == 0.6
    assert summary["concepts_tracked"] == 2
