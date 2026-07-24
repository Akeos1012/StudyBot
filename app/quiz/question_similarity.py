"""
Question similarity utilities.

Responsible for detecting whether a newly generated question is too similar
to questions already stored in the cache.
"""

from difflib import SequenceMatcher
from typing import Dict, List


def normalize(text: str) -> str:
    """Normalize text for comparison."""
    text = text.lower()

    replacements = {
        "what": "",
        "which": "",
        "does": "",
        "is": "",
        "are": "",
        "the": "",
        "of": "",
        "these": "",
        "this": "",
        "that": "",
        "a": "",
        "an": "",
    }

    for word, replacement in replacements.items():
        text = text.replace(word, replacement)

    return " ".join(text.split())


def similarity(a: str, b: str) -> float:
    """Return similarity score between two strings (0.0–1.0)."""
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def is_similar_to_pool(
    question: Dict,
    pool: List[Dict],
    threshold: float = 0.80,
) -> bool:

    new_question = normalize(question.get("question", ""))
    new_answer = normalize(question.get("correct_text") or question.get("correct", ""))
    new_fact = normalize(question.get("supporting_fact", ""))

    for existing in pool:

        old_question = normalize(existing.get("question", ""))
        old_answer = normalize(
            existing.get("correct_text") or existing.get("correct", "")
        )
        old_fact = normalize(existing.get("supporting_fact", ""))

        question_similarity = similarity(new_question, old_question)

        answer_similarity = similarity(new_answer, old_answer)

        fact_similarity = similarity(new_fact, old_fact)

        if question_similarity >= threshold and new_answer == old_answer:
            print(f"❌ Removed duplicate question: {new_question}")
            return True

        # Same concept is allowed.
        # Only reject if the supporting fact AND wording are almost identical.

        if (
            answer_similarity >= 0.95
            and fact_similarity >= 0.92
            and question_similarity >= 0.75
        ):
            print(
                f"❌ Removed duplicate concept/question pattern: {new_question}"
            )
            return True

    return False
