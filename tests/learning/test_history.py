import pytest
import os
import json
from app.learning.history_storage import HistoryStorage
from app.learning.history_service import HistoryService
from app.models.user_context import UserContext

@pytest.fixture
def test_history_storage():
    storage_path = "test_learning_history.jsonl"
    if os.path.exists(storage_path):
        os.remove(storage_path)
    yield HistoryStorage(storage_path)
    if os.path.exists(storage_path):
        os.remove(storage_path)

def test_history_record_creation(test_history_storage):
    service = HistoryService(test_history_storage)
    user_context = UserContext(user_id="user1")
    service.record_attempt(user_context, "q1", "Topic", "Concept", True)
    
    attempts = test_history_storage.get_all_attempts()
    assert len(attempts) == 1
    assert attempts[0]["user_id"] == "user1"

def test_history_append_multiple_attempts(test_history_storage):
    service = HistoryService(test_history_storage)
    user_context = UserContext(user_id="user1")
    service.record_attempt(user_context, "q1", "Topic", "Concept", True)
    service.record_attempt(user_context, "q2", "Topic", "Concept", False)
    
    attempts = test_history_storage.get_all_attempts()
    assert len(attempts) == 2
    assert attempts[0]["question_id"] == "q1"
    assert attempts[1]["question_id"] == "q2"

def test_history_user_isolation(test_history_storage):
    service = HistoryService(test_history_storage)
    u1 = UserContext(user_id="user1")
    u2 = UserContext(user_id="user2")
    service.record_attempt(u1, "q1", "Topic", "Concept", True)
    service.record_attempt(u2, "q2", "Topic", "Concept", False)
    
    attempts = test_history_storage.get_all_attempts()
    user_ids = {a["user_id"] for a in attempts}
    assert user_ids == {"user1", "user2"}

def test_history_validation(test_history_storage):
    service = HistoryService(test_history_storage)
    user_context = UserContext(user_id="user1")
    
    # Missing question_id
    service.record_attempt(user_context, None, "Topic", "Concept", True)
    # Missing concept
    service.record_attempt(user_context, "q1", "Topic", None, True)
    # Missing correct
    service.record_attempt(user_context, "q1", "Topic", "Concept", None)
    
    assert len(test_history_storage.get_all_attempts()) == 0
