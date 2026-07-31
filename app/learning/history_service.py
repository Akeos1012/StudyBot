from datetime import datetime
from typing import Optional
from app.models.user_context import UserContext
from app.learning.history_storage import HistoryStorage

class HistoryService:
    def __init__(self, storage: HistoryStorage):
        self.storage = storage

    def record_attempt(
        self,
        user_context: UserContext,
        question_id: str,
        topic: str,
        concept: str,
        correct: Optional[bool]
    ):
        if not user_context.user_id or not question_id or not concept or correct is None:
            return

        attempt = {
            "user_id": user_context.user_id,
            "question_id": question_id,
            "topic": topic,
            "concept": concept,
            "correct": correct,
            "timestamp": datetime.utcnow().isoformat()
        }

        self.storage.append_attempt(attempt)
