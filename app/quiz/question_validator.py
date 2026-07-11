# app/quiz/question_validator.py
"""
Question Validator Module - Validates generated questions.

This module provides validation functions for questions.
It does NOT generate or modify questions.
"""

from typing import Dict, Any

from .options_parser import (
    get_correct_text_from_options,
    extract_option_text,
)
from ..models.question_schema import validate_question_schema  # FIXED: Import from models


def is_valid_question(question: Dict[str, Any]) -> bool:
    """
    Validate a question for caching and usage.

    Checks:
    - Schema validity (using question_schema.py)
    - Has correct_text
    - Has supporting_fact
    - Has source_note and fact_id
    - Supporting fact is not a placeholder or invalid
    - Explanation is not empty

    Returns:
        True if valid, False otherwise
    """
    if not question or not isinstance(question, dict):
        return False

    # 1. Schema validation
    if not validate_question_schema(question):
        return False

    # 2. Required fields for grounding
    required_grounding = ["correct_text", "supporting_fact", "source_note", "fact_id"]
    for field in required_grounding:
        if field not in question or not question[field]:
            return False

    # 3. Supporting fact must be clean
    supporting_fact = str(question.get("supporting_fact", ""))
    if not supporting_fact or len(supporting_fact.split()) < 3:
        return False

    # 4. Check for invalid markers in supporting fact
    invalid_markers = ['#', '[[', ']]', '---', 'http', 'https']
    for marker in invalid_markers:
        if marker in supporting_fact:
            return False

    # 5. Explanation must exist
    explanation = question.get("explanation", "")
    if not explanation or len(explanation.split()) < 2:
        return False

    # 6. Correct text must exist
    correct_letter = question.get("correct", "")
    options = question.get("options", [])
    correct_text = get_correct_text_from_options(options, correct_letter)
    if not correct_text:
        return False

    # 7. Options must be non-empty
    for opt in question.get("options", []):
        if not opt or not extract_option_text(opt):
            return False

    return True


def has_grounded_explanation(question: Dict[str, Any]) -> bool:
    """
    Check if the explanation is grounded in the supporting fact.

    Returns:
        True if explanation mentions the correct answer or supporting fact
    """
    explanation = question.get("explanation", "").lower()
    supporting_fact = question.get("supporting_fact", "").lower()
    correct_text = question.get("correct_text", "").lower()

    if not explanation or not supporting_fact or not correct_text:
        return False

    # Check if correct answer appears in explanation
    if correct_text in explanation:
        return True

    # Check if supporting fact words appear in explanation
    fact_words = set(supporting_fact.split())
    expl_words = set(explanation.split())
    overlap = fact_words & expl_words

    return len(overlap) >= 2