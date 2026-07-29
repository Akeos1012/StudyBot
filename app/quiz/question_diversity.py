"""
Question Diversity Engine

Purpose:
    Controls variation of question cognitive styles.

Responsibilities:
    - Select question types
    - Prevent repetitive question patterns
    - Track diversity strategy

Does NOT:
    - Generate questions
    - Call LLM
    - Validate answers
"""


import random
from typing import Dict, Any, List

from .question_types import QuestionType


QUESTION_TYPE_POOL = [
    QuestionType.DEFINITION,
    QuestionType.COMPARISON,
    QuestionType.APPLICATION,
    QuestionType.SCENARIO,
    QuestionType.RELATIONSHIP,
    QuestionType.RECOGNITION,
    QuestionType.ERROR_DETECTION,
    QuestionType.CAUSE_EFFECT,
    QuestionType.CLASSIFICATION,
]



def select_question_type(
    history: list[str] = None
) -> str:
    """
    Select a question style while avoiding repetition.
    """

    history = history or []

    available = [
        q.value
        for q in QUESTION_TYPE_POOL
        if q.value not in history[-3:]
    ]

    if not available:
        available = [
            q.value
            for q in QUESTION_TYPE_POOL
        ]

    return random.choice(available)

def calculate_diversity_score(candidate: Dict[str, Any], current_batch: List[Dict[str, Any]]) -> float:
    """
    Calculate a diversity score (0.0 to 1.0) for a candidate question 
    relative to the current generation batch.
    """
    if not current_batch:
        return 1.0

    scores = []
    
    # 1. Concept diversity (Highest impact)
    candidate_concept = candidate.get("concept", "unknown")
    concept_matches = sum(1 for q in current_batch if q.get("concept") == candidate_concept)
    scores.append(1.0 if concept_matches == 0 else 0.0)
    
    # 2. Difficulty diversity
    candidate_difficulty = candidate.get("difficulty", "medium")
    difficulty_matches = sum(1 for q in current_batch if q.get("difficulty") == candidate_difficulty)
    scores.append(1.0 / (difficulty_matches + 1))
    
    # 3. Question type diversity
    candidate_type = candidate.get("type", "multiple_choice")
    type_matches = sum(1 for q in current_batch if q.get("type") == candidate_type)
    scores.append(1.0 / (type_matches + 1))
    
    return sum(scores) / len(scores)