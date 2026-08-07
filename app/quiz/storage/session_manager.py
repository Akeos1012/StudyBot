import json
import os
from typing import Dict, Optional, List
from app.models.quiz_session import QuizSession, SessionStatus

class SessionManager:
    def __init__(self, storage_path: str = "quiz_sessions.json"):
        self.storage_path = storage_path
        self._sessions: Dict[str, QuizSession] = {}
        self._load_sessions()

    def _load_sessions(self):
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                for sid, sdata in data.items():
                    self._sessions[sid] = QuizSession(**sdata)

    def _save_sessions(self):
        with open(self.storage_path, 'w') as f:
            json.dump({sid: s.model_dump() for sid, s in self._sessions.items()}, f, default=str)

    def create_session(self, user_id: str, topic: str, difficulty: str, question_ids: List[str]) -> QuizSession:
        session = QuizSession(user_id=user_id, topic=topic, difficulty=difficulty, question_ids=question_ids)
        self._sessions[session.session_id] = session
        self._save_sessions()
        return session

    def get_session(self, session_id: str) -> Optional[QuizSession]:
        return self._sessions.get(session_id)

    def update_session(self, session: QuizSession):
        self._sessions[session.session_id] = session
        self._save_sessions()

session_manager = SessionManager()
