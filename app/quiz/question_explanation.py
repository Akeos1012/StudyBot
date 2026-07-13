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

    # Fix joined words like Virtualmachines -> Virtual machines
    supporting_fact = re.sub(
        r"([a-z])([A-Z])",
        r"\1 \2",
        supporting_fact
    )

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

            supporting_words = supporting_lower.split()

            if (
                correct_lower in supporting_lower
                or any(
                    word in supporting_words
                    for word in words
                )
            ):
                clean_fact = supporting_fact

                if clean_fact.lower().startswith(correct_text.lower()):

                    remaining = clean_fact[len(correct_text):].strip()

                    plural_terms = [
                        "virtual machines",
                        "cloud databases",
                        "cloud platforms",
                        "object storage",
                    ]

                    if correct_text.lower() in plural_terms:
                        clean_fact = (
                            "they " + remaining
                        )
                    else:
                        clean_fact = (
                            "it " + remaining
                        )

                explanation = (
                    f"{correct_text} is correct because {clean_fact}"
                )

                if len(explanation.split()) <= MAX_EXPLANATION_WORDS:
                    return clean_explanation_text(explanation)

    if context:
        cleaned_context = normalize_supporting_fact(context)

        if cleaned_context:
            explanation = (
                f"{correct_text} is correct because {cleaned_context}"
            )

            if len(explanation.split()) <= MAX_EXPLANATION_WORDS:
                return explanation

    return ""

def clean_explanation_text(text: str) -> str:
    """
    Final cleanup for generated explanations.
    """

    if not text:
        return ""

    text = re.sub(
        r'(\w)(storesdata|create|provide)',
        r'\1 \2',
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r'\s+',
        ' ',
        text
    )

    text = text.strip()

    if not text.endswith('.'):
        text += '.'

    return text