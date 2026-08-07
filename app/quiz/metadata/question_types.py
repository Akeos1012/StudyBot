"""
Question Type Definitions

Purpose:
    Defines supported question generation strategies.

Responsibilities:
    - Provide question categories
    - Control question diversity

Does NOT:
    - Generate questions
    - Call LLM
    - Validate answers
"""

from enum import Enum


class QuestionType(str, Enum):
    """
    Cognitive styles used for question generation.
    """

    DEFINITION = "definition"

    COMPARISON = "comparison"

    APPLICATION = "application"

    SCENARIO = "scenario"

    RELATIONSHIP = "relationship"

    RECOGNITION = "recognition"

    ERROR_DETECTION = "error_detection"

    CAUSE_EFFECT = "cause_effect"

    CLASSIFICATION = "classification"