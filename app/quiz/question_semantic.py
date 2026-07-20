"""
Semantic validation for generated quiz questions.

This module checks:
- redundant options
- explanation consistency
- garbled text
"""

import logging
import re
from typing import Dict

from .options_parser import (
    extract_option_text,
    extract_option_letter,
    get_correct_text_from_options,
)
from .question_constants import GENERIC_PHRASES

logger = logging.getLogger(__name__)


def has_redundant_options(options: list[str]) -> bool:
    """Check if one option contains another option."""
    texts = [extract_option_text(opt).lower() for opt in options]

    for i, text in enumerate(texts):
        for j, other in enumerate(texts):
            if i != j and len(other) > 3 and other in text:
                logger.warning(f"Option overlap: '{other}' found inside '{text}'")
                return True

    for i, text in enumerate(texts):
        parts = [p.strip() for p in text.split(",")]
        if len(parts) > 2:
            for j, other in enumerate(texts):
                if i != j and any(other in part for part in parts):
                    logger.warning(
                        f"Option contains parts of another option: '{text}' contains '{other}'"
                    )
                    return True

    return False


def explanation_contradicts_answer(question: dict) -> bool:
    """Check if the explanation text actually supports the marked-correct option."""
    correct_letter = question.get("correct", "")
    options = question.get("options", [])
    explanation = question.get("explanation", "").strip().lower()

    if not options or not correct_letter:
        return True

    correct_text = get_correct_text_from_options(options, correct_letter)
    if not correct_text:
        return True

    if not explanation:
        return False
    
    # Reject explanations that mention a different answer letter
    letter_match = re.search(
        r"\b(?:the\s+)?correct\s+answer\s+is\s+([a-d])\b",
        explanation,
    )

    if letter_match:
        explained_letter = letter_match.group(1).upper()

        if explained_letter != correct_letter:
            logger.warning(
                f"Explanation says answer is {explained_letter}, "
                f"but correct option is {correct_letter}"
            )
            return True

    if letter_match:
        explained_letter = letter_match.group(1)

        if explained_letter != correct_letter:
            logger.warning(
                f"Explanation says answer is {explained_letter}, "
                f"but correct option is {correct_letter}"
            )
            return True

    correct_text_lower = correct_text.lower()
    explanation_words = [w for w in re.split(r"[^a-z0-9]+", explanation) if len(w) > 2]
    correct_words = [
        w for w in re.split(r"[^a-z0-9]+", correct_text_lower) if len(w) > 2
    ]

    if not correct_words:
        return True

    # Check if explanation supports another option more strongly
    other_option_texts = []
    for opt in options:
        opt_letter = extract_option_letter(opt)
        if opt_letter and opt_letter != correct_letter:
            opt_text = extract_option_text(opt).lower()
            if opt_text:
                other_option_texts.append(opt_text)

    for other_text in other_option_texts:
        other_words = [w for w in re.split(r"[^a-z0-9]+", other_text) if len(w) > 2]
        if not other_words:
            continue
        other_overlap = set(explanation_words) & set(other_words)
        correct_overlap = set(explanation_words) & set(correct_words)
        if len(other_overlap) > len(correct_overlap):
            logger.warning(
                f"Explanation appears to support another option: '{other_text}'"
            )
            return True

    # Reject explanations that don't mention the correct answer
    if len(correct_overlap := set(explanation_words) & set(correct_words)) < 1:
        logger.warning(
            f"Explanation doesn't mention the correct answer text: '{correct_text}'"
        )
        return True

    # Reject generic explanations that don't provide grounding
    if any(phrase in explanation for phrase in GENERIC_PHRASES):
        if len(correct_overlap) < 2:
            logger.warning(f"Explanation is too generic to support '{correct_text}'")
            return True
    return False


def has_garbled_text(text: str) -> bool:
    """Check if text contains non-printable or control characters."""
    if not isinstance(text, str):
        return True
    return bool(re.search(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]", text))


def validate_semantic(question: Dict) -> bool:
    """
    Run all semantic validation checks.

    Returns:
        True if the question passes semantic validation.
    """
    if has_redundant_options(question.get("options", [])):
        return False

    if explanation_contradicts_answer(question):
        return False

    if has_garbled_text(question.get("question", "")):
        return False

    for opt in question.get("options", []):
        if has_garbled_text(str(opt)):
            return False

    return True
