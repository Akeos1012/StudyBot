"""
Shared constants used across the quiz system.
"""

from typing import Final


# ==========================================
# GENERIC EXPLANATION PHRASES
# ==========================================

GENERIC_PHRASES: Final[list[str]] = [
    "the correct answer is",
    "because it is the correct answer",
    "because it is correct",
    "this option is correct",
    "this answer is correct",
    "the answer is",
]


# ==========================================
# GROUNDING LIMITS
# ==========================================

MAX_SUPPORTING_WORDS: Final[int] = 24
MIN_SUPPORTING_WORDS: Final[int] = 3


# ==========================================
# QUESTION LIMITS
# ==========================================

MAX_QUESTION_LENGTH: Final[int] = 250
MAX_EXPLANATION_WORDS: Final[int] = 24


# ==========================================
# CONCEPT HIERARCHY
# Used for topic relevance validation
# ==========================================

CONCEPT_HIERARCHY: Final[dict[str, list[str]]] = {

    "cloud": [
        "cloud storage",
        "cloud database",
        "cloud computing",
        "cloud infrastructure",
        "virtual machine",
        "data center",
        "edge computing",
        "serverless",
        "containerization",
        "block storage",
        "object storage",
        "file storage",
    ],

    "database": [
        "sql",
        "nosql",
        "relational",
        "mongodb",
        "postgresql",
        "mysql",
        "query",
        "indexing",
        "normalization",
    ],

    "algorithm": [
        "sorting",
        "searching",
        "recursion",
        "dynamic programming",
        "greedy",
        "backtracking",
        "divide and conquer",
        "complexity",
    ],

    "programming": [
        "function",
        "variable",
        "class",
        "object",
        "inheritance",
        "polymorphism",
        "encapsulation",
        "oop",
        "functional programming",
    ],
}


# ==========================================
# COMMON STOP WORDS
# ==========================================

STOP_WORDS: Final[set[str]] = {
    "the",
    "a",
    "an",
    "of",
    "to",
    "in",
    "on",
    "for",
    "and",
    "or",
    "is",
    "are",
    "was",
    "were",
    "with",
    "by",
    "from",
    "as",
    "at",
}


# ==========================================
# EXPORTS
# ==========================================

__all__ = [
    "GENERIC_PHRASES",
    "MAX_SUPPORTING_WORDS",
    "MIN_SUPPORTING_WORDS",
    "MAX_QUESTION_LENGTH",
    "MAX_EXPLANATION_WORDS",
    "CONCEPT_HIERARCHY",
    "STOP_WORDS",
]