"""
Shared constants used across the quiz system.
"""

from typing import Final

# Generic explanation phrases
GENERIC_PHRASES: Final[list[str]] = [
    "the correct answer is",
    "because it is the correct answer",
    "because it is correct",
    "this option is correct",
    "this answer is correct",
    "the answer is",
]

# Grounding
MAX_SUPPORTING_WORDS: Final[int] = 24
MIN_SUPPORTING_WORDS: Final[int] = 3

# Question limits
MAX_QUESTION_LENGTH: Final[int] = 250
MAX_EXPLANATION_WORDS: Final[int] = 24

# Common stop words
STOP_WORDS: Final[set[str]] = {
    "the", "a", "an", "of", "to", "in", "on", "for",
    "and", "or", "is", "are", "was", "were",
    "with", "by", "from", "as", "at",
}

__all__ = [
    "GENERIC_PHRASES",
    "MAX_SUPPORTING_WORDS",
    "MIN_SUPPORTING_WORDS",
    "MAX_QUESTION_LENGTH",
    "MAX_EXPLANATION_WORDS",
    "STOP_WORDS",
]