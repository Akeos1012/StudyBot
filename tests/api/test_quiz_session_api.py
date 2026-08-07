import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from app.api.quiz_routes import setup_routes

@pytest.fixture
def client():
    mock_quiz_service = MagicMock()
    mock_session_service = MagicMock()
    mock_metadata_loader = MagicMock()
    
    # Mock some data
    mock_metadata_loader.get_notes_by_topic.return_value = [{"topic": "Python", "path": "p.md"}]
    
    mock_metadata = []
    
    # Create a fresh app for each test and setup routes with mocks
    test_app = FastAPI()
    router = setup_routes(
        mock_quiz_service,
        mock_session_service,
        mock_metadata_loader,
        mock_metadata
    )
    test_app.include_router(router)
    
    # Mock create_quiz_session to return a session
    from app.models.quiz_session import QuizSession, SessionStatus
    mock_session = QuizSession(
        session_id="s1",
        user_id="user1",
        topic="Python",
        difficulty="medium",
        question_ids=["q1", "q2"],
        status=SessionStatus.ACTIVE
    )
    mock_quiz_service.create_quiz_session.return_value = mock_session
    mock_session_service.get_session.return_value = mock_session
    
    return TestClient(test_app), mock_quiz_service, mock_session_service

def test_create_session(client):
    api_client, _, _ = client
    response = api_client.post("/quiz/session/create", json={
        "topic": "Python",
        "difficulty": "medium",
        "count": 2
    }, headers={"X-User-ID": "user1"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "s1"

def test_get_session(client):
    api_client, _, mock_session_service = client
    
    get_response = api_client.get(f"/quiz/session/s1", headers={"X-User-ID": "user1"})
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["session_id"] == "s1"

def test_complete_session(client):
    api_client, _, mock_session_service = client
    
    # Complete
    response = api_client.patch(f"/quiz/session/s1/complete", headers={"X-User-ID": "user1"})
    assert response.status_code == 200
    # The status check should be on the session returned by the service
    mock_session_service.complete_session.assert_called_with("s1")
