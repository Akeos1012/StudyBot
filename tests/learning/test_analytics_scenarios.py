import pytest
import sqlite3
from app.learning.analytics.db_manager import DBManager
from app.learning.analytics.analytics_repository import AnalyticsRepository
from app.learning.analytics.analytics_service import LearningAnalyticsService
from app.learning.recommendation.recommendation_service import RecommendationService
from app.learning.recommendation.recommendation_engine import RecommendationEngine

@pytest.fixture
def test_setup():
    db_manager = DBManager(db_path=":memory:")
    repository = AnalyticsRepository(db_manager)
    analytics_service = LearningAnalyticsService(repository)
    engine = RecommendationEngine()
    recommendation_service = RecommendationService(analytics_service, engine)
    
    # Insert mock data
    conn = db_manager.get_connection()
    conn.execute("INSERT INTO users (user_id) VALUES ('user_improving')")
    conn.execute("INSERT INTO learning_events (user_id, topic, concept, correct, timestamp) VALUES ('user_improving', 'Database', 'Normalization', 1, '2026-08-01 10:00:00')")
    conn.execute("INSERT INTO mastery_records (user_id, concept, attempts, correct_count, mastery_score) VALUES ('user_improving', 'Normalization', 1, 1, 1.0)")
    conn.commit()
    
    return analytics_service, recommendation_service

def test_improving_learner(test_setup):
    analytics, recs = test_setup
    # Verify mastery and recommendation for improving user
    mastery = analytics.get_mastery_summary("user_improving")
    assert mastery["overall_mastery"] > 0
    
    recs_list = recs.get_recommendations("user_improving")
    assert isinstance(recs_list, list)

def test_new_user_scenario(test_setup):
    analytics, recs = test_setup
    # New user not in DB
    summary = analytics.get_mastery_summary("new_user")
    assert summary["total_attempts"] == 0
    
    recs_list = recs.get_recommendations("new_user")
    assert len(recs_list) == 0
