import pytest
import os
import json
from app.learning.mastery_storage import MasteryStorage
from app.learning.mastery_service import MasteryService
from app.models.user_context import UserContext

@pytest.fixture
def test_storage():
    storage_path = "test_mastery_data.json"
    if os.path.exists(storage_path):
        os.remove(storage_path)
    yield MasteryStorage(storage_path)
    if os.path.exists(storage_path):
        os.remove(storage_path)

def test_storage_save_load(test_storage):
    user_id = "user1"
    records = {"concept1": {"attempts": 1, "correct": 1, "wrong": 0, "mastery": 1.0, "recommended_difficulty": "hard"}}
    test_storage.save_user_records(user_id, records)
    assert test_storage.get_user_records(user_id) == records

def test_mastery_service_update(test_storage):
    service = MasteryService(test_storage)
    user_context = UserContext(user_id="user1")
    concept = "concept1"
    
    # Correct answer
    service.update_mastery(user_context, concept, True)
    records = test_storage.get_user_records(user_context.user_id)
    assert records[concept]["attempts"] == 1
    assert records[concept]["correct"] == 1
    assert records[concept]["mastery"] == 1.0
    
    # Wrong answer
    service.update_mastery(user_context, concept, False)
    records = test_storage.get_user_records(user_context.user_id)
    assert records[concept]["attempts"] == 2
    assert records[concept]["correct"] == 1
    assert records[concept]["wrong"] == 1
    assert records[concept]["mastery"] == 0.5
