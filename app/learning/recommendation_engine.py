from typing import List, Dict, Any

class RecommendationEngine:
    WEAK_CONCEPT_WEIGHT = +2
    STRONG_CONCEPT_WEIGHT = -1
    DEFAULT_WEIGHT = 0

    def get_concept_weights(
        self,
        weak_concepts: List[str],
        strong_concepts: List[str]
    ) -> Dict[str, int]:
        """
        Generates concept-based priority weights.
        """
        weights = {c: self.WEAK_CONCEPT_WEIGHT for c in weak_concepts}
        weights.update({c: self.STRONG_CONCEPT_WEIGHT for c in strong_concepts})
        return weights

    def rank_questions(
        self,
        questions: List[Dict[str, Any]],
        weak_concepts: List[str],
        strong_concepts: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Ranks questions based on personalization scores.
        Stable sort is used to preserve relative order for equal scores.
        """
        def get_score(q: Dict[str, Any]) -> int:
            concept = q.get("concept")
            if concept in weak_concepts:
                return self.WEAK_CONCEPT_WEIGHT
            elif concept in strong_concepts:
                return self.STRONG_CONCEPT_WEIGHT
            return self.DEFAULT_WEIGHT

        # Python's sort is stable, preserving original order for equal scores.
        # We sort descending by score.
        return sorted(questions, key=get_score, reverse=True)
