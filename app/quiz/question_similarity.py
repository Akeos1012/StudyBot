"""
Question similarity utilities.

Responsible for detecting whether a newly generated question is too similar
to questions already stored in the cache.
"""

from difflib import SequenceMatcher
from typing import Dict, List


def normalize(text: str) -> str:
    """Normalize text for comparison."""
    return " ".join(text.lower().split())


def similarity(a: str, b: str) -> float:
    """Return similarity score between two strings (0.0–1.0)."""
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def is_similar_to_pool(
    question: Dict,
    pool: List[Dict],
    threshold: float = 0.90,
) -> bool:
    """
    Return True if the question is too similar to an existing question.
    """
    new_text = question.get("question", "")

    for existing in pool:
        old_text = existing.get("question", "")

        if similarity(new_text, old_text) >= threshold:
            return True

    return False