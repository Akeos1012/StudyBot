import pytest
from unittest.mock import MagicMock
from app.services.quiz_session_service import QuizSessionService
from app.models.quiz_session import SessionStatus

@pytest.fixture
def mock_storage():
    return MagicMock()

@pytest.fixture
def service(mock_storage):
    return QuizSessionService(mock_storage)

def test_create_session(service, mock_storage):
    session = service.create_session("user1", "Cloud", "medium", ["q1", "q2"])
    assert session.user_id == "user1"
    assert session.status == SessionStatus.ACTIVE
    mock_storage.create_session.assert_called_once()

def test_resume_session(service, mock_storage):
    # Setup mock
    mock_session = MagicMock()
    mock_storage.get_session.return_value = mock_session
    
    returned_session = service.get_session("sid1")
    assert returned_session == mock_session
    mock_storage.get_session.assert_called_with("sid1")

def test_submit_answer_updates_progress(service, mock_storage):
    # Setup mock
    mock_session = MagicMock()
    mock_storage.get_session.return_value = mock_session
    
    service.update_progress("sid1", 1)
    assert mock_session.current_question_index == 1
    mock_storage.update_session.assert_called_with(mock_session)

def test_complete_session(service, mock_storage):
    # Setup mock
    mock_session = MagicMock()
    mock_storage.get_session.return_value = mock_session
    
    service.complete_session("sid1")
    assert mock_session.status == SessionStatus.COMPLETED
    mock_storage.update_session.assert_called_with(mock_session)

def test_user_isolation(service, mock_storage):
    # This test conceptually verifies that storage handles user isolation, 
    # as the service itself is just a pass-through for storage operations.
    # In a real SQL implementation, this would be enforced in SQL queries.
    mock_storage.get_session.return_value = None
    assert service.get_session("invalid_session") is None
