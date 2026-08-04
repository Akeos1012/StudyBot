from app.learning.analytics.analytics_repository import AnalyticsRepository
from app.learning.analytics.analytics_service import LearningAnalyticsService
from app.learning.analytics.db_manager import DBManager


def test_repository_persists_events_and_service_uses_them_for_progress_and_trend():
    db_manager = DBManager(db_path=":memory:")
    repository = AnalyticsRepository(db_manager)
    service = LearningAnalyticsService(repository)

    repository.record_learning_event(
        user_id="user-1",
        session_id="session-1",
        event_type="answer",
        topic="Databases",
        concept="SQL",
        correct=True,
        difficulty="medium",
        response_time_ms=420,
    )
    repository.record_learning_event(
        user_id="user-1",
        session_id="session-1",
        event_type="answer",
        topic="Databases",
        concept="SQL",
        correct=False,
        difficulty="medium",
        response_time_ms=500,
    )
    repository.record_learning_event(
        user_id="user-1",
        session_id="session-2",
        event_type="answer",
        topic="Algorithms",
        concept="Sorting",
        correct=True,
        difficulty="hard",
        response_time_ms=300,
    )

    progress = service.get_progress_summary("user-1")
    assert progress["total_questions_answered"] == 3
    assert progress["correct_answers"] == 2
    assert progress["accuracy_percentage"] == 66.67
    assert "Databases" in progress["topics_studied"]

    trend = service.get_learning_trend("user-1", 30)
    assert len(trend["trend"]) == 1
    assert trend["trend"][0]["accuracy"] == 66.67
