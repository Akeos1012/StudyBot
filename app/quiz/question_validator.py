"""
Question Validator Module - Validates generated questions.

This module provides validation functions for questions.
It does NOT generate or modify questions.
"""

import re
from typing import Dict, Any
from difflib import SequenceMatcher

from .options_parser import (
    get_correct_text_from_options,
    extract_option_text,
    extract_option_letter,
)

from .validation_logger import log_validation_failure

from .question_constants import (
    MAX_QUESTION_LENGTH
)

from ..models.question_schema import validate_question_schema


# ==========================================
# CACHE VALIDATION
# ==========================================

def is_valid_question(question: Dict[str, Any]) -> bool:
    """
    Validate a question for caching and usage.
    """

    if not question or not isinstance(question, dict):
        return False

    if not validate_question_schema(question):
        return False

    required_grounding = [
        "correct_text",
        "supporting_fact",
        "source_note",
        "fact_id"
    ]

    for field in required_grounding:
        if field not in question or not question[field]:
            return False

    supporting_fact = str(question.get("supporting_fact", ""))

    if not supporting_fact:
        return False

    if len(supporting_fact.split()) < 3:
        return False

    invalid_markers = [
        '#',
        '[[',
        ']]',
        '---',
        'http',
        'https'
    ]

    for marker in invalid_markers:
        if marker in supporting_fact:
            return False

    explanation = question.get("explanation", "")

    if not explanation or len(explanation.split()) < 2:
        return False

    correct_letter = question.get("correct", "")
    options = question.get("options", [])

    correct_text = get_correct_text_from_options(
        options,
        correct_letter
    )

    if not correct_text:
        return False

    for opt in options:
        if not opt or not extract_option_text(opt):
            return False

    return True



def has_grounded_explanation(question: Dict[str, Any]) -> bool:
    """
    Check if explanation is grounded in supporting fact.
    """

    explanation = question.get("explanation", "").lower()
    supporting_fact = question.get("supporting_fact", "").lower()
    correct_text = question.get("correct_text", "").lower()

    if not explanation or not supporting_fact or not correct_text:
        return False

    if correct_text in explanation:
        return True

    fact_words = set(supporting_fact.split())
    explanation_words = set(explanation.split())

    overlap = fact_words & explanation_words

    return len(overlap) >= 2



# ==========================================
# STRUCTURE VALIDATION
# ==========================================

def validate_structure(question: dict) -> bool:

    required = [
        'question',
        'options',
        'correct',
        'explanation'
    ]

    missing = [
        field
        for field in required
        if field not in question
    ]

    if missing:
        log_validation_failure(
            question,
            "structure",
            f"Missing required fields: {missing}"
        )
        return False


    if (
        not isinstance(question['options'], list)
        or len(question['options']) != 4
    ):
        log_validation_failure(
            question,
            "structure",
            "Options must contain exactly 4 items"
        )
        return False


    q_text = question['question'].strip()


    if not q_text.endswith("?"):
        log_validation_failure(
            question,
            "structure",
            "Question does not end with '?'"
        )
        return False


    if len(q_text) > MAX_QUESTION_LENGTH:
        log_validation_failure(
            question,
            "structure",
            "Question exceeds maximum length"
        )
        return False


    if re.search(r'\b[A-D]\)', q_text):
        log_validation_failure(
            question,
            "structure",
            "Question contains leaked option markers"
        )
        return False


    return True



# ==========================================
# CORRECT ANSWER VALIDATION
# ==========================================

def normalize_and_validate_correct_field(question: dict) -> bool:

    correct = str(
        question.get("correct", "")
    ).strip()

    options = question.get(
        "options",
        []
    )


    if len(options) != 4:
        return False


    if correct in [
        "A",
        "B",
        "C",
        "D"
    ]:
        return True


    match = re.match(
        r'^([A-D])[\)\.\-\s]',
        correct
    )

    if match:
        question["correct"] = match.group(1)
        return True


    for option in options:

        option_letter = extract_option_letter(option)
        option_text = extract_option_text(option)

        if option_text.lower() == correct.lower():
            question["correct"] = option_letter
            return True


    log_validation_failure(
        question,
        "correct_field",
        "Unable to resolve correct answer"
    )

    return False



# ==========================================
# QUESTION FOCUS VALIDATION
# ==========================================

def validate_question_focus(
    question: dict,
    concept: str
) -> bool:

    q_text = question.get(
        "question",
        ""
    ).lower()

    concept_lower = concept.lower()


    if (
        "layer" in q_text
        and "layer" not in concept_lower
    ):
        return False


    if concept_lower in q_text:
        return True


    words = [
        w
        for w in concept_lower.split()
        if len(w) > 3
    ]


    if words:

        matched = sum(
            1
            for word in words
            if word in q_text
        )

        if matched / len(words) < 0.5:
            return False


    return True



# ==========================================
# TOPIC RELEVANCE
# ==========================================

def is_relevant_to_topic(
    question: str,
    topic: str,
    answer: str = "",
    supporting_fact: str = ""
) -> bool:

    combined = " ".join(
        [
            question or "",
            answer or "",
            supporting_fact or ""
        ]
    ).lower()


    if supporting_fact:

        words = [
            w.lower()
            for w in re.findall(
                r"[A-Za-z][A-Za-z0-9\-]{3,}",
                supporting_fact
            )
        ]

        overlap = sum(
            1
            for word in set(words)
            if word in combined
        )

        if overlap >= 2:
            return True


    if answer:

        words = [
            w.lower()
            for w in re.findall(
                r"[A-Za-z][A-Za-z0-9\-]{2,}",
                answer
            )
        ]

        if any(word in combined for word in words):
            return True


    topic_lower = topic.lower()


    if topic_lower in combined:
        return True


    for word in topic_lower.split():

        if len(word) > 3 and word in combined:
            return True


    log_validation_failure(
        None,
        "topic_relevance",
        "Question not related to topic"
    )

    return False

def is_duplicate_question(
    new_question: str,
    existing_questions: list[str],
    threshold: float = 0.85
) -> bool:

    new_question = new_question.lower().strip()

    for old_question in existing_questions:

        similarity = SequenceMatcher(
            None,
            new_question,
            old_question.lower().strip()
        ).ratio()

        if similarity >= threshold:
            return True

    return False