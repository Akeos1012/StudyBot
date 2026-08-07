from typing import Optional
from app.models.user_context import UserContext
from app.learning.analytics.analytics_repository import AnalyticsRepository

class HistoryService:
    def __init__(self, repository: AnalyticsRepository):
        self.repository = repository

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

        self.repository.record_learning_event(
            user_id=user_context.user_id,
            session_id=question_id, # Using question_id as session_id for now as it seems the intent
            event_type="quiz_attempt",
            topic=topic,
            concept=concept,
            correct=correct,
            difficulty=None,
            response_time_ms=None
        )
