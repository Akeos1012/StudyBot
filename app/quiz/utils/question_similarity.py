"""
MODULE: Question Similarity

LOCATION:
app/quiz/question_similarity.py


PIPELINE POSITION:

Generated Question
        |
        v
Question Similarity Check
        |
        +------------+
        |            |
        v            v
Duplicate      Unique
 Reject         Accept
                    |
                    v
             Question Cache


MAIN PURPOSE:

Compare newly generated questions against existing questions
to prevent duplicates from entering the question pool.

This module only measures similarity.

It NEVER:
- generates questions
- edits questions
- validates correctness
- scores quality


INPUT:
- Newly generated question
- Existing question pool

OUTPUT:
True  -> duplicate detected
False -> sufficiently unique


CONNECTED MODULES:

Used by:
- quiz_generator.py
- question_cache.py

Dependencies:
- Python SequenceMatcher


AUDIT STATUS:
CORE DEDUPLICATION MODULE
Changes affect cache diversity.
"""

import re
from difflib import SequenceMatcher
from typing import Dict, List

# ============================================================================
# TEXT NORMALIZATION CHECKPOINT
#
# Purpose:
# Normalize question text before similarity comparison.
#
# Removes common filler words so comparison focuses on
# the important technical content.
#
# Example:
#
# "What is Cloud Storage?"
#
# becomes
#
# "cloud storage"
#
# Connected:
# similarity()
# is_similar_to_pool()
# ============================================================================

def normalize(text: str) -> str:
    """Normalize text for comparison."""
    text = text.lower()

    replacements = {
        "what": "",
        "which": "",
        "does": "",
        "is": "",
        "are": "",
        "the": "",
        "of": "",
        "these": "",
        "this": "",
        "that": "",
        "a": "",
        "an": "",
    }

    for word, replacement in replacements.items():
        text = re.sub(r"\b" + re.escape(word) + r"\b", replacement, text)

    return " ".join(text.split())

# ============================================================================
# SIMILARITY SCORING CHECKPOINT
#
# Purpose:
# Calculate similarity between two normalized strings.
#
# Returns:
# 0.0 = completely different
# 1.0 = identical
#
# Uses:
# Python SequenceMatcher
#
# Connected:
# is_similar_to_pool()
# ============================================================================

def similarity(a: str, b: str) -> float:
    """Return similarity score between two strings (0.0–1.0)."""
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()

# ============================================================================
# DUPLICATE POOL CHECKPOINT
#
# Purpose:
# Prevent duplicate questions from entering the cache.
#
# Comparison uses three dimensions:
#
# 1. Question wording
# 2. Correct answer
# 3. Supporting fact
#
# Rejection Rules:
#
# - Same wording + same answer
# - Nearly identical wording generated from the same fact
#
# Same concept is allowed if the supporting fact and wording
# are sufficiently different.
#
# Pipeline:
#
# QuizGenerator
#      |
#      v
# Generated Question
#      |
#      v
# is_similar_to_pool()
#      |
#      +--> Duplicate → Reject
#      |
#      +--> Unique → Cache
#
# Connected:
# - quiz_generator.py
# - question_cache.py
# ============================================================================

def is_similar_to_pool(
    question: Dict,
    pool: List[Dict],
    threshold: float = 0.80,
) -> bool:

    new_question = normalize(question.get("question", ""))
    new_answer = normalize(question.get("correct_text") or question.get("correct", ""))
    new_fact = normalize(question.get("supporting_fact", ""))

    for existing in pool:

        old_question = normalize(existing.get("question", ""))
        old_answer = normalize(
            existing.get("correct_text") or existing.get("correct", "")
        )
        old_fact = normalize(existing.get("supporting_fact", ""))

        question_similarity = similarity(new_question, old_question)

        answer_similarity = similarity(new_answer, old_answer)

        fact_similarity = similarity(new_fact, old_fact)

        if question_similarity >= threshold and new_answer == old_answer:
            print(f"❌ Removed duplicate question: {new_question}")
            return True

        # Same concept is allowed.
        # Only reject if the supporting fact AND wording are almost identical.

        if (
            answer_similarity >= 0.95
            and fact_similarity >= 0.92
            and question_similarity >= 0.75
        ):
            print(
                f"❌ Removed duplicate concept/question pattern: {new_question}"
            )
            return True

    return False
