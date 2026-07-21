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

            raw_fact = str(
                fact.get("supporting_fact")
                or fact.get("sentence")
                or fact.get("definition")
                or ""
            )

            supporting_fact = normalize_supporting_fact(raw_fact)

            # Remove duplicated concept prefix from explanation source
            prefix_patterns = [
                rf"^{re.escape(correct_text)}\s*[-–:]\s*",
                rf"^{re.escape(correct_text)}\s+",
            ]

            for pattern in prefix_patterns:
                supporting_fact = re.sub(
                    pattern,
                    "",
                    supporting_fact,
                    flags=re.IGNORECASE
                ).strip()

            print("\n=== EXPLANATION DEBUG ===")
            print("Correct:", correct_text)
            print("Fact:", supporting_fact[:200])
            print("=========================")

            if not supporting_fact:
                continue

            supporting_lower = supporting_fact.lower()
            correct_lower = correct_text.lower()

            words = [
                word for word in re.split(r"[^a-z0-9]+", correct_lower) if len(word) > 2
            ]

            supporting_words = [
                word.rstrip(".,;:\"'“”()[]")
                for word in re.split(r"\s+", supporting_lower)
            ]

            if (
                correct_lower in supporting_lower
                or any(
                    word.rstrip("s") in {
                        w.rstrip("s")
                        for w in supporting_words
                    }
                    for word in words
                )
                or any(
                    word.rstrip("s") in supporting_lower
                    for word in words
                )
                or len(supporting_words) >= 8
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
                            if clean_fact.lower().startswith(
                                (
                                    "refers to ",
                                    "is ",
                                    "are ",
                                    "means ",
                                    "describes ",
                                )
                            ):
                                explanation = f"{correct_text} {clean_fact}"

                            else:
                                explanation = (
                                    f"{correct_text} is correct because {clean_fact}"
                                )

                if len(explanation.split()) > MAX_EXPLANATION_WORDS:
                    explanation = limit_explanation_length(explanation)

                return clean_explanation_text(explanation)

    if context:
        cleaned_context = normalize_supporting_fact(context)

        if cleaned_context:
            explanation = (
                f"{correct_text} is correct because {cleaned_context}"
)

            if len(explanation.split()) > MAX_EXPLANATION_WORDS:
                sentences = explanation.split(".")
                explanation = sentences[0].strip() + "."

            return explanation

    return ""

def remove_fact_prefix(text: str, correct_text: str) -> str:
    """
    Remove duplicated concept names only from raw facts.
    """

    if not text:
        return ""

    prefix = correct_text.strip()

    if text.lower().startswith(prefix.lower()):
        remainder = text[len(prefix):].strip()

        if remainder.startswith(("–", "-")):
            remainder = remainder[1:].strip()

        return f"{prefix} {remainder}".strip()

    return text

def limit_explanation_length(text: str, max_words: int = MAX_EXPLANATION_WORDS) -> str:
    """
    Trim explanation without cutting sentences in half.
    """
    if not text:
        return ""

    sentences = re.split(r"(?<=[.!?])\s+", text.strip())

    result = []

    for sentence in sentences:
        if len((" ".join(result) + " " + sentence).split()) <= max_words:
            result.append(sentence)
        else:
            break

    if result:
        return " ".join(result)

    # fallback if first sentence is too long
    words = text.split()[:max_words]

    trimmed = " ".join(words)

    if not trimmed.endswith((".", "!", "?")):
        trimmed += "..."

    return trimmed

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

    if not text.endswith((".", "!", "?")):
        text += "."

    return text
