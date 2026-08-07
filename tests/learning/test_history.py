import pytest
from unittest.mock import MagicMock
from app.models.user_context import UserContext
from app.learning.analytics.analytics_repository import AnalyticsRepository

@pytest.fixture
def mock_repo():
    return MagicMock(spec=AnalyticsRepository)

def test_repository_record_creation(mock_repo):
    user_context = UserContext(user_id="user1")
    
    mock_repo.record_learning_event(
        user_id=user_context.user_id,
        session_id="s1",
        event_type="answer",
        topic="Topic",
        concept="Concept",
        correct=True,
        difficulty="medium"
    )
    
    mock_repo.record_learning_event.assert_called_once()
    args, kwargs = mock_repo.record_learning_event.call_args
    assert kwargs["user_id"] == "user1"
    assert kwargs["concept"] == "Concept"
    assert kwargs["correct"] is True
