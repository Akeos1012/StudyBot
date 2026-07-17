"""
Question Validator Module - Validates generated questions.

This module provides validation functions for questions.
It does NOT generate or modify questions.
"""

import re
from typing import Dict, Any, List
from difflib import SequenceMatcher

from .options_parser import (
    get_correct_text_from_options,
    extract_option_text,
    extract_option_letter,
)

from .validation_logger import log_validation_failure

from .question_constants import MAX_QUESTION_LENGTH

from ..models.question_schema import validate_question_schema

# ==========================================
# CONSTANTS
# ==========================================

# Common words to ignore in concept matching
STOP_WORDS = {
    'the', 'this', 'that', 'these', 'those', 'a', 'an',
    'of', 'for', 'with', 'without', 'from', 'to', 'by',
    'on', 'at', 'in', 'into', 'through', 'during'
}

# Invalid single-word concepts (verbs, adjectives, generic terms)
INVALID_CONCEPT_WORDS = {
    'allows', 'provides', 'enables', 'stores', 'manages', 'reduces', 'improves',
    'uses', 'supports', 'offers', 'helps', 'contains', 'includes', 'does', 'doing',
    'responsible', 'processing', 'maintaining', 'organizing', 'allow', 'provide',
    'enable', 'store', 'manage', 'reduce', 'improve', 'use', 'support', 'offer',
    'help', 'contain', 'include', 'do', 'concept', 'example', 'method', 'approach',
    'technique', 'process', 'system', 'layer', 'type', 'category', 'classification',
    'service', 'platform', 'solution', 'resource', 'infrastructure', 'component',
    'module', 'thing', 'item', 'element', 'part', 'way', 'means', 'mechanism'
}

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

    required_grounding = ["correct_text", "supporting_fact", "source_note", "fact_id"]

    for field in required_grounding:
        if field not in question or not question[field]:
            return False

    supporting_fact = str(question.get("supporting_fact", ""))

    if not supporting_fact:
        return False

    if len(supporting_fact.split()) < 3:
        return False

    invalid_markers = ["#", "[[", "]]", "---", "http", "https"]

    for marker in invalid_markers:
        if marker in supporting_fact:
            return False

    explanation = question.get("explanation", "")

    if not explanation or len(explanation.split()) < 2:
        return False

    correct_letter = question.get("correct", "")
    options = question.get("options", [])

    correct_text = get_correct_text_from_options(options, correct_letter)

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

    required = ["question", "options", "correct", "explanation"]

    missing = [field for field in required if field not in question]

    if missing:
        log_validation_failure(
            question, "structure", f"Missing required fields: {missing}"
        )
        return False

    if not isinstance(question["options"], list) or len(question["options"]) != 4:
        log_validation_failure(
            question, "structure", "Options must contain exactly 4 items"
        )
        return False

    q_text = question["question"].strip()

    if not q_text.endswith("?"):
        log_validation_failure(question, "structure", "Question does not end with '?'")
        return False

    if len(q_text) > MAX_QUESTION_LENGTH:
        log_validation_failure(question, "structure", "Question exceeds maximum length")
        return False

    if re.search(r"\b[A-D]\)", q_text):
        log_validation_failure(
            question, "structure", "Question contains leaked option markers"
        )
        return False

    return True


# ==========================================
# CORRECT ANSWER VALIDATION
# ==========================================


def normalize_and_validate_correct_field(question: dict) -> bool:

    correct = str(question.get("correct", "")).strip()

    options = question.get("options", [])

    if len(options) != 4:
        return False

    if correct in ["A", "B", "C", "D"]:
        return True

    match = re.match(r"^([A-D])[\)\.\-\s]", correct)

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
        question, "correct_field", "Unable to resolve correct answer"
    )

    return False


# ==========================================
# QUESTION FOCUS VALIDATION
# ==========================================


def _normalize_text(text: str) -> str:
    """
    Normalize text for comparison: lowercase, remove punctuation, collapse spaces.
    """
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _extract_meaningful_words(text: str) -> List[str]:
    """
    Extract meaningful words from text (exclude stop words and short words).
    """
    words = _normalize_text(text).split()
    return [w for w in words if len(w) > 2 and w not in STOP_WORDS]


def validate_question_focus(
    question: dict,
    concept: str,
    supporting_fact: str = ""
) -> bool:
    """
    Validate that the generated question focuses on the correct concept.
    Uses flexible matching: normalized text comparison, meaningful word overlap.
    """
    q_text = question.get("question", "")
    concept_lower = concept.lower()

    # Rule 1: If question uses "layer" but concept doesn't, reject
    if "layer" in q_text.lower() and "layer" not in concept_lower:
        log_validation_failure(
            question, "focus", f"Question uses 'layer' but concept is '{concept}'"
        )
        return False

    # Normalize both texts
    q_normalized = _normalize_text(q_text)
    concept_normalized = _normalize_text(concept)

    # Rule 2: Exact phrase appears in question
    if concept_normalized in q_normalized:
        return True

    # NEW: Ignore spaces ("Cloud Database" == "clouddatabase")
    compact_question = q_normalized.replace(" ", "")
    compact_concept = concept_normalized.replace(" ", "")

    if compact_concept in compact_question:
        return True

    # Rule 3: Require most meaningful words, not just 50%
    concept_words = set(_extract_meaningful_words(concept))
    q_words = set(_extract_meaningful_words(q_text))

    if concept_words:
        overlap = len(concept_words & q_words) / len(concept_words)

        if overlap >= 0.6:
            return True

    if concept_words:
        matched = sum(1 for w in concept_words if w in q_words)
        match_ratio = matched / len(concept_words)

        # If at least 50% of concept words appear in question, accept
        if match_ratio >= 0.5:
            return True

        # If we have some matches but not enough, log for debugging
        if match_ratio > 0:
            print(f"⚠️ Partial concept match for '{concept}': {match_ratio:.0%}")

    # Rule 4: Check if key concept words appear in any meaningful form
    # Example: "Cloud Storage" -> "storage" appears in "Which service allows users to store files?"
    concept_words_lower = [w.lower() for w in concept.split()]
    q_text_lower = q_text.lower()

    # Rule 4: Stem-like matching
    for concept_word in concept_words:
        for q_word in q_words:
            if (
                concept_word.startswith(q_word)
                or q_word.startswith(concept_word)
            ):
                return True

    log_validation_failure(
        question, "focus", f"Question doesn't reference concept '{concept}'"
    )
    return False


# ==========================================
# TOPIC RELEVANCE
# ==========================================


def is_relevant_to_topic(
    question: str, topic: str, answer: str = "", supporting_fact: str = ""
) -> bool:

    combined = " ".join([question or "", answer or "", supporting_fact or ""]).lower()

    if supporting_fact:

        words = [
            w.lower() for w in re.findall(r"[A-Za-z][A-Za-z0-9\-]{3,}", supporting_fact)
        ]

        overlap = sum(1 for word in set(words) if word in combined)

        if overlap >= 2:
            return True

    if answer:

        words = [w.lower() for w in re.findall(r"[A-Za-z][A-Za-z0-9\-]{2,}", answer)]

        if any(word in combined for word in words):
            return True

    topic_lower = topic.lower()

    if topic_lower in combined:
        return True

    for word in topic_lower.split():

        if len(word) > 3 and word in combined:
            return True

    log_validation_failure(None, "topic_relevance", "Question not related to topic")

    return False


# ==========================================
# DUPLICATE DETECTION
# ==========================================


def _normalize_question_text(text: str) -> str:
    """
    Normalize question text for duplicate detection.
    Removes punctuation, extra whitespace, and common filler phrases.
    """
    text = text.lower().strip()
    # Remove punctuation (keep letters, numbers, spaces)
    text = re.sub(r'[^\w\s]', ' ', text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove common filler phrases
    filler_phrases = ['what is', 'which of the following', 'which one', 'the question']
    for phrase in filler_phrases:
        if text.startswith(phrase):
            text = text[len(phrase):].strip()
    return text


def is_duplicate_question(
    new_question: str, existing_questions: List[str], threshold: float = 0.85
) -> bool:
    """
    Check if a question is a duplicate of existing questions.
    Uses SequenceMatcher after normalizing both texts.
    """
    if not new_question or not existing_questions:
        return False

    new_normalized = _normalize_question_text(new_question)

    for old_question in existing_questions:
        if not old_question:
            continue

        old_normalized = _normalize_question_text(old_question)

        # If the normalized text is empty, skip
        if not new_normalized or not old_normalized:
            continue

        similarity = SequenceMatcher(None, new_normalized, old_normalized).ratio()

        if similarity >= threshold:
            print(f"⚠️ Duplicate question detected (similarity: {similarity:.2f})")
            return True

    return False


# ==========================================
# CONCEPT VALIDATION
# ==========================================


def is_valid_concept(concept: str) -> bool:
    """
    Check if a concept is valid for fallback generation.
    Rejects: verbs, adjectives, generic single words, vague categories.
    Accepts: technical nouns, multi-word concepts, acronyms.
    """
    if not concept:
        return False

    concept_clean = concept.strip()
    if not concept_clean:
        return False

    concept_lower = concept_clean.lower()
    words = concept_lower.split()

    # Reject: Single generic word
    if len(words) == 1:
        # Allow common acronyms (2+ uppercase letters)
        if concept_clean.isupper() and len(concept_clean) >= 2:
            return True

        # Reject: verbs, adjectives, generic terms
        if concept_lower in INVALID_CONCEPT_WORDS:
            return False

        # Reject: short words that are likely generic
        if len(concept_lower) < 4:
            return False

    # Reject: concepts that are obviously generic phrases
    generic_phrases = [
        'allows for', 'provides a', 'enables the', 'uses a', 'supports the',
        'method of', 'process of', 'system for', 'type of', 'category of'
    ]

    for phrase in generic_phrases:
        if phrase in concept_lower:
            return False

    # Reject: concepts that start with verbs
    verb_start_patterns = [
        r'^allows?\s+', r'^provides?\s+', r'^enables?\s+',
        r'^stores?\s+', r'^manages?\s+', r'^reduces?\s+',
        r'^improves?\s+', r'^uses?\s+', r'^supports?\s+',
        r'^offers?\s+', r'^helps?\s+', r'^contains?\s+',
        r'^includes?\s+', r'^does?\s+', r'^focuses?\s+'
    ]

    for pattern in verb_start_patterns:
        if re.match(pattern, concept_lower):
            return False

    # Accept: multi-word concepts (2+ words)
    if len(words) >= 2:
        # But reject if they end with generic terms
        generic_endings = ['concept', 'example', 'method', 'approach', 'technique',
                           'process', 'system', 'layer', 'type', 'category',
                           'classification', 'service', 'platform', 'solution',
                           'resource', 'infrastructure', 'component', 'module']

        if words[-1] in generic_endings:
            # Allow if it's a known concept like "Operating System"
            if len(words) >= 3:
                return True
            # Reject "Storage System" but allow "Distributed Storage System"
            if len(words) == 2:
                return words[0] not in ['abstract', 'generic', 'basic', 'simple']

    # Accept: all other multi-word concepts
    if len(words) >= 2:
        return True

    # Accept: single word that is capitalized (likely a proper noun)
    if concept_clean[0].isupper() and len(concept_clean) > 2:
        return True

    # Default: accept if it passes all checks
    return True