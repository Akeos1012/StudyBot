import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from app.main import app
from app.api.routes import setup_routes

@pytest.fixture
def client(monkeypatch):
    mock_quiz_service = MagicMock()
    mock_smart_reviewer_service = MagicMock()
    mock_metadata_loader = MagicMock()
    mock_metadata = []
    mock_quiz_session_service = MagicMock()
    
    # Create a fresh app for each test and setup routes with mocks
    from fastapi import FastAPI
    test_app = FastAPI()
    router = setup_routes(
        mock_quiz_service, 
        mock_quiz_session_service,
        mock_metadata_loader, 
        mock_metadata, 
        smart_reviewer_service=mock_smart_reviewer_service
    )
    test_app.include_router(router)
    
    return TestClient(test_app), mock_quiz_service, mock_smart_reviewer_service

def test_review_success(client):
    api_client, mock_quiz, mock_reviewer = client
    
    # Setup mock data
    question_id = "test-q-1"
    mock_question = {
        "question_id": question_id,
        "fact_id": "f1",
        "supporting_fact": "Fact content",
        "source_note": "note.md",
        "explanation": "Stored explanation",
        "correct": "A",
        "concept": "Test Concept",
        "topic": "Test Topic"
    }
    mock_quiz.quiz_generator.cache.get_question_by_id.return_value = mock_question
    
    from app.models.smart_reviewer_schema import SmartReviewerResult
    mock_reviewer.generate_review.return_value = SmartReviewerResult(
        question_id=question_id,
        user_answer="B",
        correct_answer="A",
        is_correct=False,
        explanation="Stored explanation",
        supporting_fact="Fact content",
        source_note="note.md",
        fact_id="f1",
        related_concepts=["Related 1", "Related 2"]
    )
    
    response = api_client.post("/quiz/review", json={
        "question_id": question_id,
        "user_answer": "B"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_correct"] is False
    assert data["correct_answer"] == "A"
    assert data["explanation"] == "Stored explanation"
    assert "Related 1" in data["related_concepts"]

def test_review_question_not_found(client):
    api_client, mock_quiz, mock_reviewer = client
    mock_quiz.quiz_generator.cache.get_question_by_id.return_value = None
    
    response = api_client.post("/quiz/review", json={
        "question_id": "missing",
        "user_answer": "Any"
    })
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

def test_review_invalid_input(client):
    api_client, _, _ = client
    
    # Missing question_id
    response = api_client.post("/quiz/review", json={
        "user_answer": "Any"
    })
    assert response.status_code == 422
    
    # Missing user_answer
    response = api_client.post("/quiz/review", json={
        "question_id": "q1"
    })
    assert response.status_code == 422

def test_review_service_error(client):
    api_client, mock_quiz, mock_reviewer = client
    mock_quiz.quiz_generator.cache.get_question_by_id.return_value = {"question_id": "q1"}
    mock_reviewer.generate_review.side_effect = Exception("Service failed")
    
    response = api_client.post("/quiz/review", json={
        "question_id": "q1",
        "user_answer": "A"
    })
    
    assert response.status_code == 500
    assert "Internal error" in response.json()["detail"]
