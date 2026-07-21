"""
Unified Question Schema Contract
All questions must follow this structure.

This module provides:
- Schema definition for questions
- Validation logic with detailed error reporting
- Type checking for all fields
- Normalization of the correct answer field
"""

from typing import List, Dict, Any, Optional, Type, Union

# ============================================================================
# CONSTANTS
# ============================================================================

# ===== Schema Field Definitions =====
REQUIRED_MC_FIELDS = ["question", "options", "correct", "explanation"]

REQUIRED_FILL_BLANK_FIELDS = [
    "question",
    "correct",
    "type",
    "supporting_fact",
    "concept",
]

REQUIRED_MC_FIELDS = [
    "question",
    "options",
    "correct",
    "explanation"
]
OPTIONAL_FIELDS = [
    "_is_fallback",
    "source_notes",
    "concept_type",
    "difficulty",
    # Grounding fields
    "correct_text",
    "supporting_fact",
    "fact_id",
    "source_note",
    # Quality metadata
    "_quality_score",
    "_quality_scores",
]

# ===== Field Type Mappings =====
FIELD_TYPES: Dict[str, Union[Type, List[Type]]] = {
    "question": str,
    "options": list,
    "correct": str,
    "explanation": str,
    "_is_fallback": bool,
    "source_notes": list,
    "concept_type": str,
    "difficulty": str,
    # Grounding fields
    "correct_text": str,
    "supporting_fact": str,
    "fact_id": str,
    "source_note": str,
    # Quality metadata
    "_quality_score": float,
    "_quality_scores": dict,
}

# ===== Validation Constants =====
VALID_OPTIONS_COUNT = 4
VALID_CORRECT_LETTERS = {"A", "B", "C", "D"}

# ===== Error Messages =====
ERROR_MISSING_REQUIRED = "Missing required field: {field}"
ERROR_EMPTY_FIELD = "Empty field: {field}"
ERROR_INVALID_OPTIONS_COUNT = "Must have exactly 4 options, got {count}"
ERROR_INVALID_CORRECT = "Correct must be A-D, got: {value}"
ERROR_WRONG_TYPE = "Field '{field}' must be of type {expected_type}, got {actual_type}"
ERROR_OPTION_EMPTY = "Option at index {index} is empty or contains only whitespace"


# ============================================================================
# INTERNAL HELPERS
# ============================================================================


def _normalize_correct(correct: Any) -> str:
    """Normalize the correct answer to uppercase, stripped."""
    return str(correct).strip().upper()


def _get_field_type(field_name: str) -> Optional[Union[Type, List[Type]]]:
    """Get the expected type for a field."""
    return FIELD_TYPES.get(field_name)


def _validate_field_type(value: Any, field_name: str) -> bool:
    """Validate that a value matches its expected type."""
    expected_type = _get_field_type(field_name)
    if expected_type is None:
        return True  # Unknown fields are allowed
    return isinstance(value, expected_type)


def _validate_options(options: Any) -> bool:
    """Validate the options field."""

    if not isinstance(options, list):
        return False

    if len(options) != VALID_OPTIONS_COUNT:
        print(ERROR_INVALID_OPTIONS_COUNT.format(count=len(options)))
        return False

    expected_letters = ["A", "B", "C", "D"]

    for i, opt in enumerate(options):

        if not isinstance(opt, dict):
            return False

        if "id" not in opt or "text" not in opt:
            return False

        if opt["id"] != expected_letters[i]:
            return False

        if not isinstance(opt["text"], str):
            return False

        if not opt["text"].strip():
            print(ERROR_OPTION_EMPTY.format(index=i))
            return False

    return True


def _validate_correct(correct: Any) -> bool:
    """Validate the correct field."""
    normalized = _normalize_correct(correct)
    if normalized not in VALID_CORRECT_LETTERS:
        print(ERROR_INVALID_CORRECT.format(value=correct))
        return False
    return True


def _validate_required_fields(question: Dict[str, Any]) -> bool:
    """Validate required fields based on question type."""

    question_type = question.get("type", "mcq")

    if question_type == "fill_blank":
        required_fields = REQUIRED_FILL_BLANK_FIELDS
    else:
        required_fields = REQUIRED_MC_FIELDS

    for field in required_fields:
        if field not in question:
            print(ERROR_MISSING_REQUIRED.format(field=field))
            return False

        value = question.get(field)
        if not value or not str(value).strip():
            print(ERROR_EMPTY_FIELD.format(field=field))
            return False

    return True


def _validate_optional_fields(question: Dict[str, Any]) -> bool:
    """Validate optional fields if present."""
    for field in OPTIONAL_FIELDS:
        if field in question:
            if not _validate_field_type(question[field], field):
                expected = _get_field_type(field)
                actual = type(question[field]).__name__
                print(
                    ERROR_WRONG_TYPE.format(
                        field=field,
                        expected_type=expected.__name__ if expected else "unknown",
                        actual_type=actual,
                    )
                )
                return False

    return True


# ============================================================================
# PUBLIC API
# ============================================================================

QUESTION_SCHEMA = {
    "required": REQUIRED_MC_FIELDS,
    "optional": OPTIONAL_FIELDS,
    "types": FIELD_TYPES,
}


def validate_question_schema(question: Dict[str, Any]) -> bool:
    """
    Validate a question against the schema.

    Args:
        question: Dictionary containing the question data

    Returns:
        True if valid, False otherwise with error messages printed

    Validation checks:
        1. All required fields are present and non-empty
        2. Optional fields have correct types if present
        3. Options is a list of exactly 4 non-empty strings
        4. Correct is one of A, B, C, D (case-insensitive)
        5. All string fields contain non-whitespace content
    """
    # Step 1: Validate required fields
    if not _validate_required_fields(question):
        return False

    # Step 2: Validate field types for optional fields
    if not _validate_optional_fields(question):
        return False

    # Step 3: Validate based on question type
    if question.get("type") == "fill_blank":

        # Fill blank questions do not use options or A/B/C/D answers
        if not question.get("question"):
            return False

        if not question.get("correct"):
            return False

    else:
        # MCQ validation
        if not _validate_options(question.get("options", [])):
            return False

        if not _validate_correct(question.get("correct", "")):
            return False

    # Step 4: Normalize correct only for MCQ
    if question.get("type") != "fill_blank":
        question["correct"] = _normalize_correct(question["correct"])

    return True
