"""
Question Explanation Module

Responsible for creating consistent grounded explanations.
"""

import re
from typing import List, Dict, Any
from .text_normalizer import normalize_supporting_fact

MAX_EXPLANATION_WORDS = 30


def build_consistent_explanation(
    question_text: str,
    options: List[str],
    correct_letter: str,
    correct_text: str,
    context: str = "",
    facts: List[Dict[str, Any]] = None,
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
                word for word in re.split(r"[^a-z0-9]+", correct_lower) if len(word) > 2
            ]

            supporting_words = supporting_lower.split()

            if correct_lower in supporting_lower or any(
                word in supporting_words for word in words
            ):
                clean_fact = supporting_fact

                if clean_fact.lower().startswith(correct_text.lower()):
                    clean_fact = clean_fact[len(correct_text):].strip()

                    if clean_fact:
                        explanation = f"{correct_text} {clean_fact}"
                    else:
                        explanation = f"{correct_text} is confirmed by the supporting fact."
                else:
                    clean_fact_lower = clean_fact.lower()
                    correct_lower = correct_text.lower()

                    if clean_fact_lower.startswith(correct_lower):
                        clean_fact = clean_fact[len(correct_text) :].strip()

                        if clean_fact:
                            explanation = f"{correct_text} {clean_fact}"
                        else:
                            explanation = f"{correct_text} is correct because the supporting fact confirms it."

                    else:
                        if clean_fact.lower().startswith(
                            (
                                "is ",
                                "are ",
                                "provides ",
                                "allows ",
                                "stores ",
                                "creates ",
                            )
                        ):
                            explanation = f"{correct_text} {clean_fact}"
                        else:
                            explanation = clean_fact

                if len(explanation.split()) > MAX_EXPLANATION_WORDS:
                    explanation = " ".join(
                        explanation.split()[:MAX_EXPLANATION_WORDS]
                    ) + "."

                return clean_explanation_text(explanation)

    if context:
        cleaned_context = normalize_supporting_fact(context)

        if cleaned_context:
            explanation = cleaned_context

            if len(explanation.split()) > MAX_EXPLANATION_WORDS:
                explanation = " ".join(
                    explanation.split()[:MAX_EXPLANATION_WORDS]
                ) + "."

            return explanation

    return ""


def clean_explanation_text(text: str) -> str:
    """
    Final cleanup for generated explanations.
    """

    if not text:
        return ""

    text = re.sub(
        r"(\w)(storesdata|create|provide)", r"\1 \2", text, flags=re.IGNORECASE
    )

    text = re.sub(r"\s+", " ", text)

    text = re.sub(r"(\b[A-Za-z ]+)\s+\1\b", r"\1", text, flags=re.IGNORECASE)

    text = text.strip()

    if not text.endswith("."):
        text += "."

    return text
