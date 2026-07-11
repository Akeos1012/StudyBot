"""
Question Explanation Module

Responsible for creating consistent grounded explanations.
"""

import re
from typing import List, Dict, Any


MAX_EXPLANATION_WORDS = 30


def normalize_supporting_fact(supporting_fact: str) -> str:
    """
    Clean and normalize supporting facts for explanations.
    """

    if not supporting_fact:
        return ""

    supporting_fact = supporting_fact.strip()

    supporting_fact = re.sub(
        r"([a-z])([A-Z])",
        r"\1 \2",
        supporting_fact
    )

    return supporting_fact


def build_consistent_explanation(
    question_text: str,
    options: List[str],
    correct_letter: str,
    correct_text: str,
    context: str = "",
    facts: List[Dict[str, Any]] = None
) -> str:
    """
    Build a short explanation from a selected supporting fact.
    """

    if not correct_text:
        return ""

    correct_text = correct_text.strip()

    if not correct_text:
        return ""

    if facts:
        for fact in facts:

            supporting_fact = normalize_supporting_fact(
                str(
                    fact.get("supporting_fact")
                    or fact.get("sentence")
                    or fact.get("definition")
                    or ""
                )
            )

            if not supporting_fact:
                continue

            supporting_lower = supporting_fact.lower()
            correct_lower = correct_text.lower()

            words = [
                word
                for word in re.split(
                    r"[^a-z0-9]+",
                    correct_lower
                )
                if len(word) > 2
            ]

            if (
                correct_lower in supporting_lower
                or any(
                    word in supporting_lower
                    for word in words
                )
            ):
                explanation = (
                    f"{correct_text} is correct because {supporting_fact}"
                )

                if len(explanation.split()) <= MAX_EXPLANATION_WORDS:
                    return explanation

    if context:
        cleaned_context = normalize_supporting_fact(context)

        if cleaned_context:
            explanation = (
                f"{correct_text} is correct because {cleaned_context}"
            )

            if len(explanation.split()) <= MAX_EXPLANATION_WORDS:
                return explanation

    return ""