import pytest
from unittest.mock import MagicMock
from app.learning.analytics_service import LearningAnalyticsService
from app.learning.mastery_storage import MasteryStorage
from app.learning.history_storage import HistoryStorage

@pytest.fixture
def analytics_service():
    mock_mastery = MagicMock(spec=MasteryStorage)
    mock_history = MagicMock(spec=HistoryStorage)
    
    # Setup mock mastery records
    mock_mastery.get_user_records.return_value = {
        "concept1": {"attempts": 10, "correct": 8, "wrong": 2, "mastery": 0.8}, # Accuracy 0.8
        "concept2": {"attempts": 10, "correct": 4, "wrong": 6, "mastery": 0.4}  # Accuracy 0.4
    }
    
    return LearningAnalyticsService(mock_mastery, mock_history)

def test_concept_statistics(analytics_service):
    stats = analytics_service.get_concept_statistics("user1")
    
    assert "concept1" in stats
    assert stats["concept1"]["accuracy"] == 0.8
    assert stats["concept1"]["mastery"] == 0.8
    
    assert "concept2" in stats
    assert stats["concept2"]["accuracy"] == 0.4
    assert stats["concept2"]["mastery"] == 0.4

def test_weak_concept_detection(analytics_service):
    # Threshold 0.6: concept2 is weak (0.4 < 0.6)
    weak = analytics_service.get_weak_concepts("user1", threshold=0.6)
    assert weak == ["concept2"]

def test_learning_summary(analytics_service):
    summary = analytics_service.get_learning_summary("user1")
    
    assert summary["weak_concepts"] == ["concept2"]
    assert summary["strong_concepts"] == ["concept1"]
    assert summary["total_attempts"] == 20
