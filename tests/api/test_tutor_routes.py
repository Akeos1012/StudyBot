import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from app.api.tutor_routes import setup_tutor_routes

@pytest.fixture
def mock_tutor_service():
    return MagicMock()

@pytest.fixture
def client(mock_tutor_service):
    app = FastAPI()
    tutor_router = setup_tutor_routes(mock_tutor_service)
    app.include_router(tutor_router)
    return TestClient(app)

def test_valid_question(client, mock_tutor_service):
    mock_tutor_service.ask.return_value = {
        "found": True,
        "answer": "Test answer",
        "sources": ["s1"],
        "related_concepts": ["C1"],
        "intent": "EXPLAIN"
    }
    
    response = client.post("/tutor/ask", json={"question": "Explain containerization"})
    
    assert response.status_code == 200
    assert response.json()["found"] is True
    assert response.json()["answer"] == "Test answer"
    mock_tutor_service.ask.assert_called_with("Explain containerization")

def test_empty_question(client, mock_tutor_service):
    mock_tutor_service.ask.return_value = {
        "found": False,
        "answer": "Please provide a valid question.",
        "sources": [],
        "related_concepts": [],
        "intent": "UNKNOWN"
    }
    
    response = client.post("/tutor/ask", json={"question": ""})
    
    assert response.status_code == 200
    assert response.json()["found"] is False

def test_unknown_topic(client, mock_tutor_service):
    mock_tutor_service.ask.return_value = {
        "found": False,
        "answer": "I couldn't find this topic in your knowledge base.",
        "sources": [],
        "related_concepts": [],
        "intent": "UNKNOWN"
    }
    
    response = client.post("/tutor/ask", json={"question": "Explain quantum computing"})
    
    assert response.status_code == 200
    assert response.json()["found"] is False
    assert "I couldn't find this topic" in response.json()["answer"]

def test_compare_intent_integration(client, mock_tutor_service):
    mock_tutor_service.ask.return_value = {
        "found": True,
        "answer": "| RAM | ROM |\n|---|---|\n| Volatile | Non-volatile |",
        "sources": ["s1"],
        "related_concepts": ["RAM", "ROM"],
        "intent": "COMPARE"
    }
    
    response = client.post("/tutor/ask", json={"question": "What is the difference between RAM and ROM?"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["found"] is True
    assert data["intent"] == "COMPARE"
    assert "RAM" in data["answer"]
    assert "ROM" in data["answer"]
    mock_tutor_service.ask.assert_called_with("What is the difference between RAM and ROM?")
