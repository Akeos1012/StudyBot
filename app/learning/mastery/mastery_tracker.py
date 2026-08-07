"""
Mastery Tracker

Purpose:
    Tracks student understanding of concepts.

Responsibilities:
    - Record correct/wrong answers
    - Calculate mastery score
    - Recommend difficulty

Does NOT:
    - Generate questions
    - Store files
    - Manage cache
"""


from typing import Dict, Any


def create_concept_record(concept: str) -> Dict[str, Any]:
    """
    Create default learning record for a concept.
    """

    return {
        "concept": concept,

        "attempts": 0,
        "correct": 0,
        "wrong": 0,

        "mastery": 0.0,

        "recommended_difficulty": "medium"
    }


def update_concept_performance(
    record: Dict[str, Any],
    correct: bool
) -> Dict[str, Any]:
    """
    Update concept mastery after answering.
    """

    record["attempts"] = (
        record.get("attempts", 0) + 1
    )

    if correct:
        record["correct"] = (
            record.get("correct", 0) + 1
        )
    else:
        record["wrong"] = (
            record.get("wrong", 0) + 1
        )

    attempts = record["attempts"]

    record["mastery"] = round(
        record["correct"] / attempts,
        2
    )

    record["recommended_difficulty"] = (
        calculate_difficulty(
            record["mastery"]
        )
    )

    return record


def calculate_difficulty(
    mastery: float
) -> str:
    """
    Convert mastery score into question difficulty.
    """

    if mastery < 0.4:
        return "easy"

    if mastery < 0.8:
        return "medium"

    return "hard"