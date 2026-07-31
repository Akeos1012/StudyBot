from typing import Dict, Any, List
from app.learning.mastery_storage import MasteryStorage
from app.learning.history_storage import HistoryStorage

class LearningAnalyticsService:
    def __init__(self, mastery_storage: MasteryStorage, history_storage: HistoryStorage):
        self.mastery_storage = mastery_storage
        self.history_storage = history_storage

    def get_concept_statistics(self, user_id: str) -> Dict[str, Any]:
        mastery_records = self.mastery_storage.get_user_records(user_id)
        stats = {}
        for concept, data in mastery_records.items():
            attempts = data.get("attempts", 0)
            correct = data.get("correct", 0)
            mastery = data.get("mastery", 0.0)
            
            accuracy = correct / attempts if attempts > 0 else 0.0
            
            stats[concept] = {
                "attempts": attempts,
                "correct": correct,
                "accuracy": accuracy,
                "mastery": mastery
            }
        return stats

    def get_weak_concepts(self, user_id: str, threshold: float = 0.6) -> List[str]:
        stats = self.get_concept_statistics(user_id)
        return [concept for concept, data in stats.items() if data["accuracy"] < threshold]

    def get_learning_summary(self, user_id: str) -> Dict[str, Any]:
        stats = self.get_concept_statistics(user_id)
        weak = self.get_weak_concepts(user_id)
        
        strong = [concept for concept in stats if concept not in weak]
        total_attempts = sum(data["attempts"] for data in stats.values())
        
        return {
            "total_attempts": total_attempts,
            "weak_concepts": weak,
            "strong_concepts": strong
        }
