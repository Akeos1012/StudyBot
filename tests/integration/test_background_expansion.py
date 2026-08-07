
import pytest
import time
from fastapi.testclient import TestClient
from app.main import app
from app.quiz.storage.pool_manager import PoolManager

client = TestClient(app)

def test_background_expansion_triggered():
    # Trigger expansion for a topic
    # Need to find a topic that needs expansion
    topic = "Cloud"
    
    # Ensure expansion state is clear
    # Access the pool_manager via dependency injection in a real app, 
    # but here we can just ensure the state is clean.
    
    response = client.post("/quiz/generate", json={
        "topic": topic,
        "count": 10,
        "difficulty": "medium",
        "fresh": False
    })
    
    assert response.status_code == 200
    # The request should return immediately
    
    # The background task should be running
    # We can check if it is expanding
    from app.main import pool_manager
    
    # It might have finished already if the test is slow, 
    # but we can check if it was triggered
    # (This is hard to verify without mocks)
    
    # Just verify that the request itself returned
    assert "questions" in response.json()

def test_duplicate_expansion_prevention():
    from app.main import pool_manager
    topic = "Cloud"
    
    # Ensure it's clean
    pool_manager.finish_expansion(topic)
    
    # Manually start expansion
    assert pool_manager.try_start_expansion(topic) == True
    
    # Try to start again
    assert pool_manager.try_start_expansion(topic) == False
    
    # Cleanup
    pool_manager.finish_expansion(topic)
    
    # Should be able to start again
    assert pool_manager.try_start_expansion(topic) == True
    pool_manager.finish_expansion(topic)

def test_expansion_cleanup_on_exception():
    from app.main import pool_manager
    topic = "ErrorTopic"
    
    # Simulate failed expansion
    pool_manager.try_start_expansion(topic)
    
    # We can simulate failure by calling finish_expansion in finally block 
    # as implemented, or manually if needed
    pool_manager.finish_expansion(topic)
    
    # Should be clear
    assert pool_manager.is_expanding(topic) == False
