import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from app.api.routes import setup_routes

@pytest.fixture
def client():
    mock_quiz_service = MagicMock()
    mock_metadata_loader = MagicMock()
    mock_metadata = []
    mock_quiz_session_service = MagicMock()
    
    # Mock data for get_knowledge_summary
    mock_quiz_service.get_knowledge_summary.return_value = {
        "topics": [
            {
                "name": "Python",
                "note_count": 10,
                "fact_count": 50,
                "last_updated": "2026-08-03T01:00:00Z",
                "status": "ready"
            }
        ],
        "total_topics": 1
    }
    
    from fastapi import FastAPI
    test_app = FastAPI()
    router = setup_routes(
        mock_quiz_service,
        mock_quiz_session_service,
        mock_metadata_loader,
        mock_metadata
    )
    test_app.include_router(router)
    
    return TestClient(test_app)

def test_get_knowledge_topics(client):
    response = client.get("/knowledge/topics")
    assert response.status_code == 200
    data = response.json()
    assert "topics" in data
    assert len(data["topics"]) == 1
    assert data["topics"][0]["name"] == "Python"
    assert data["topics"][0]["fact_count"] == 50
