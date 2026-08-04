import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_mastery_no_user():
    response = client.get("/analytics/mastery")
    assert response.status_code == 400

def test_get_mastery_with_user():
    # This will fail unless we seed data in the test db,
    # but the API should return 200/empty for new user
    response = client.get("/analytics/mastery", headers={"X-User-ID": "test_user"})
    assert response.status_code == 200
    assert response.json()["overall_mastery"] == 0.0

def test_get_weak_topics_with_user():
    response = client.get("/analytics/weak-topics", headers={"X-User-ID": "test_user"})
    assert response.status_code == 200
    assert response.json() == []
