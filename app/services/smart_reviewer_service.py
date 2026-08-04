from typing import Dict, Any, List
from app.models.smart_reviewer_schema import SmartReviewerResult
from app.rag.fact_cache import FactCache

class SmartReviewerService:
    def __init__(self, fact_cache: FactCache):
        self.fact_cache = fact_cache

    def generate_review(self, question: Dict[str, Any], user_answer: str) -> SmartReviewerResult:
        # Validate question has necessary data
        required_fields = ["question_id", "fact_id", "explanation", "correct", "concept"]
        for field in required_fields:
            if field not in question:
                raise ValueError(f"Question missing required field for review: {field}")
        
        # Determine correctness (normalize MCQ 'correct' field if necessary)
        # Assuming question['correct'] is the letter (A, B, C, D)
        correct_answer = question.get("correct")
        is_correct = user_answer.strip().upper() == correct_answer.strip().upper()
        
        # Get related concepts
        related_concepts = self._get_related_concepts(question)
        
        return SmartReviewerResult(
            question_id=question["question_id"],
            user_answer=user_answer,
            correct_answer=correct_answer,
            is_correct=is_correct,
            explanation=question["explanation"],
            supporting_fact=question.get("supporting_fact"),
            source_note=question.get("source_note"),
            fact_id=question["fact_id"],
            related_concepts=related_concepts
        )
        
    def _get_related_concepts(self, question: Dict[str, Any]) -> List[str]:
        topic = question.get("topic")
        if not topic:
            return []
            
        facts = self.fact_cache.get_facts(topic)
        
        # Return other concepts in the same topic, excluding current concept
        current_concept = question.get("concept")
        related = [
            f["concept"] for f in facts 
            if f.get("concept") and f["concept"] != current_concept
        ]
        
        # Sort and limit to 5 for V1 (deterministic order)
        return sorted(list(set(related)))[:5]
