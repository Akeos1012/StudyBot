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