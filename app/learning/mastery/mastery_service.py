from typing import Optional
from app.models.user_context import UserContext
from app.learning.analytics.analytics_repository import AnalyticsRepository
from app.learning.mastery.mastery_tracker import create_concept_record, update_concept_performance, calculate_difficulty

class MasteryService:
    def __init__(self, repository: AnalyticsRepository):
        self.repository = repository

    def update_mastery(
        self,
        user_context: UserContext,
        concept: str,
        correct: bool
    ):
        if not user_context.user_id:
            return

        user_id = user_context.user_id
        # Retrieve existing records using repository
        records = self.repository.get_mastery_records(user_id)
        
        # Find specific concept record
        concept_record = next((r for r in records if r["concept"] == concept), None)
        
        if not concept_record:
            # Map new record format if needed
            concept_record = create_concept_record(concept)
        else:
            # Map repository record to tracker format
            concept_record = {
                "concept": concept_record["concept"],
                "attempts": concept_record["attempts"],
                "correct": concept_record["correct_count"],
                "wrong": concept_record["wrong_count"],
                "mastery": concept_record["mastery_score"]
            }

        updated_record = update_concept_performance(concept_record, correct)

        # Save back to repository
        self.repository.upsert_mastery_record(
            user_id=user_id,
            concept=concept,
            attempts=updated_record["attempts"],
            correct_count=updated_record["correct"],
            wrong_count=updated_record["wrong"],
            mastery_score=updated_record["mastery"]
        )
    
    def get_recommended_difficulty(self, user_context: UserContext, topic: str) -> Optional[str]:
        if not user_context.user_id:
            return None
        records = self.repository.get_mastery_records(user_context.user_id)
        if not records:
            return None
        
        # Average mastery
        total_mastery = 0.0
        for record in records:
            total_mastery += record.get("mastery_score", 0.0)
        
        avg = total_mastery / len(records)
        return calculate_difficulty(avg)
