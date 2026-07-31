from typing import Optional
from app.models.user_context import UserContext
from app.learning.mastery_storage import MasteryStorage
from app.learning.mastery_tracker import create_concept_record, update_concept_performance, calculate_difficulty

class MasteryService:
    def __init__(self, storage: MasteryStorage):
        self.storage = storage

    def update_mastery(
        self,
        user_context: UserContext,
        concept: str,
        correct: bool
    ):
        if not user_context.user_id:
            return

        user_id = user_context.user_id
        user_records = self.storage.get_user_records(user_id)

        concept_record = user_records.get(concept)
        if not concept_record:
            concept_record = create_concept_record(concept)

        updated_record = update_concept_performance(concept_record, correct)

        user_records[concept] = updated_record
        self.storage.save_user_records(user_id, user_records)
    
    def get_recommended_difficulty(self, user_context: UserContext, topic: str) -> Optional[str]:
        if not user_context.user_id:
            return None
        records = self.storage.get_user_records(user_context.user_id)
        if not records:
            return None
        
        # Average mastery
        total_mastery = 0.0
        for record in records.values():
            total_mastery += record.get("mastery", 0.0)
        
        avg = total_mastery / len(records)
        return calculate_difficulty(avg)
