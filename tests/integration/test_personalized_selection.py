import pytest
from unittest.mock import MagicMock
from app.services.quiz_service import QuizService
from app.learning.mastery_service import MasteryService
from app.learning.history_service import HistoryService
from app.learning.analytics_service import LearningAnalyticsService
from app.learning.recommendation_engine import RecommendationEngine
from app.quiz.question_cache import QuestionCache

@pytest.fixture
def mock_cache():
    return MagicMock(spec=QuestionCache)

@pytest.fixture
def service(mock_cache):
    return QuizService(
        metadata_loader=MagicMock(),
        quiz_generator=MagicMock(cache=mock_cache),
        pool_manager=MagicMock(),
        mastery_service=MagicMock(spec=MasteryService),
        history_service=MagicMock(spec=HistoryService),
        analytics_service=MagicMock(spec=LearningAnalyticsService),
        recommendation_engine=MagicMock(spec=RecommendationEngine),
        quiz_session_service=MagicMock()
    )
def test_personalization_disabled(service, mock_cache):
    # Call with personalize=False
    service.get_or_generate_questions(topic="test", personalize=False)
    # Ensure no personalization weights passed to sample
    mock_cache.sample.assert_called_with(
        "test", "", "medium", "multiple", 3, concept_weights=None
    )

def test_weak_concept_weighting(service, mock_cache):
    # Setup analytics to return a weak concept
    service.analytics_service.get_learning_summary.return_value = {
        "weak_concepts": ["recursion"],
        "strong_concepts": []
    }
    # Setup recommendation engine to return weight
    service.recommendation_engine.get_concept_weights.return_value = {"recursion": 2}
    
    # Call with personalize=True
    service.get_or_generate_questions(topic="test", personalize=True, user_context=MagicMock(user_id="u1"))
    
    # Verify weights passed
    mock_cache.sample.assert_called_with(
        "test", "", "medium", "multiple", 3, concept_weights={"recursion": 2}
    )

def test_no_user_history(service, mock_cache):
    # Setup analytics to return empty
    service.analytics_service.get_learning_summary.return_value = {
        "weak_concepts": [],
        "strong_concepts": []
    }
    # Setup recommendation engine to return empty
    service.recommendation_engine.get_concept_weights.return_value = {}
    
    service.get_or_generate_questions(topic="test", personalize=True, user_context=MagicMock(user_id="u1"))
    
    # Weights should be empty dict
    mock_cache.sample.assert_called_with(
        "test", "", "medium", "multiple", 3, concept_weights={}
    )

def test_fallback_logic(service, mock_cache):
    # If cache.sample returns None, the fallback logic in quiz_service should trigger.
    mock_cache.sample.return_value = None
    
    # Mock generation method to verify it is called
    generated_questions = [
        {
            "question_id": "q1",
            "question": "Generated question",
            "concept": "Cloud Storage",
            "metadata": {"success_rate": 0.0}
        }
    ]
    service.generate_questions_for_topic = MagicMock(return_value=generated_questions)
    
    # Execute (should not raise exception)
    result = service.get_or_generate_questions(
        topic="test", 
        personalize=True, 
        user_context=MagicMock(user_id="u1")
    )

    # Verify fallback was triggered
    service.generate_questions_for_topic.assert_called_once()
    
    # Verify result
    assert result == generated_questions
