import pytest
from app.quiz.storage.session_manager import session_manager
from app.models.quiz_session import SessionStatus

def test_session_lifecycle():
    # 1. Create
    user_id = "test-user"
    topic = "Database"
    difficulty = "medium"
    question_ids = ["q1", "q2", "q3"]
    
    session = session_manager.create_session(user_id, topic, difficulty, question_ids)
    assert session.session_id is not None
    assert session.status == SessionStatus.ACTIVE
    
    # 2. Retrieve
    retrieved = session_manager.get_session(session.session_id)
    assert retrieved is not None
    assert retrieved.user_id == user_id
    assert retrieved.question_ids == question_ids
    
    # 3. Update
    retrieved.current_question_index = 1
    session_manager.update_session(retrieved)
    updated = session_manager.get_session(session.session_id)
    assert updated.current_question_index == 1
