from typing import List, Optional, Dict, Any
from app.models.quiz_session import QuizSession, SessionStatus
from datetime import datetime

class QuizSessionService:
    def __init__(self, storage):
        self.storage = storage

    def create_session(self, user_id: str, topic: str, difficulty: str, question_ids: List[str]) -> QuizSession:
        session = QuizSession(user_id=user_id, topic=topic, difficulty=difficulty, question_ids=question_ids)
        self.storage.create_session(session)
        return session

    def get_session(self, session_id: str) -> Optional[QuizSession]:
        return self.storage.get_session(session_id)

    def update_progress(self, session_id: str, current_question_index: int):
        session = self.get_session(session_id)
        if session:
            session.current_question_index = current_question_index
            self.storage.update_session(session)

    def complete_session(self, session_id: str):
        session = self.get_session(session_id)
        if session:
            session.status = SessionStatus.COMPLETED
            session.completed_at = datetime.now()
            self.storage.update_session(session)

    def abandon_session(self, session_id: str):
        session = self.get_session(session_id)
        if session:
            session.status = SessionStatus.ABANDONED
            self.storage.update_session(session)
