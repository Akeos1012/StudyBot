"""
Question Metadata Utilities

Purpose:
    Handles learning-related metadata attached to cached questions.

Responsibilities:
    - Create default metadata
    - Update usage statistics
    - Track answer performance

Does NOT:
    - Store cache files
    - Validate questions
    - Generate questions
"""


from datetime import datetime
from typing import Dict, Any


def create_metadata() -> Dict[str, Any]:
    """
    Create default metadata for a new cached question.
    """

    now = datetime.now().isoformat()

    return {
        "created_at": now,
        "updated_at": now,

        "usage_count": 0,
        "last_seen": None,

        "times_correct": 0,
        "times_wrong": 0,

        "success_rate": 0.0,

        "difficulty_history": [],

        "quality_score": 0.0,
    }


def update_seen(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update when a question is shown to the student.
    """

    metadata["usage_count"] = metadata.get(
        "usage_count",
        0
    ) + 1

    metadata["last_seen"] = datetime.now().isoformat()

    metadata["updated_at"] = datetime.now().isoformat()

    return metadata


def update_answer_result(
    metadata: Dict[str, Any],
    correct: bool
) -> Dict[str, Any]:
    """
    Update learning statistics after answering.
    """

    if correct:
        metadata["times_correct"] = (
            metadata.get("times_correct", 0) + 1
        )
    else:
        metadata["times_wrong"] = (
            metadata.get("times_wrong", 0) + 1
        )

    total = (
        metadata.get("times_correct", 0)
        +
        metadata.get("times_wrong", 0)
    )

    if total > 0:
        metadata["success_rate"] = round(
            metadata["times_correct"] / total,
            2
        )

    metadata["updated_at"] = datetime.now().isoformat()

    return metadata