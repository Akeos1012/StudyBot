import pytest
from app.learning.analytics.db_manager import DBManager
from app.learning.analytics.analytics_repository import AnalyticsRepository
from app.learning.analytics.analytics_service import LearningAnalyticsService

@pytest.fixture
def analytics_service():
    db_manager = DBManager(db_path=":memory:")
    repository = AnalyticsRepository(db_manager)
    return LearningAnalyticsService(repository)

def test_mastery_summary_empty(analytics_service):
    summary = analytics_service.get_mastery_summary("test_user")
    assert summary["overall_mastery"] == 0.0
    assert summary["total_attempts"] == 0

def test_progress_summary_empty(analytics_service):
    progress = analytics_service.get_progress_summary("test_user")
    assert progress["total_questions_answered"] == 0
    assert progress["accuracy_percentage"] == 0.0

def test_activity_metrics_empty(analytics_service):
    metrics = analytics_service.get_activity_metrics("test_user")
    assert metrics["total_sessions"] == 0
    assert metrics["questions_per_session"] == 0.0
