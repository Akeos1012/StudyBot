"""
MODULE: Question Validator

LOCATION:
app/quiz/question_validator.py

PIPELINE POSITION:
QuizGenerator
      |
      v
LLM Generated Question
      |
      v
QuestionValidator
      |
      +--> Accept
      |
      +--> Reject

MAIN PURPOSE:
Validate generated quiz questions before they are:
- scored
- cached
- returned to users

CORE RULE:
This module NEVER creates questions.
It only checks:
- structure
- correctness
- grounding requirements
- uniqueness
- concept quality
- ambiguity

INPUT:
- Generated question dictionary

OUTPUT:
True  -> question accepted
False -> question rejected
"""

import logging
import re
from typing import Dict, Any, List, Set, Optional
from difflib import SequenceMatcher

from .options_parser import (
    get_correct_text_from_options,
    extract_option_text,
    extract_option_letter,
)
from .validation_logger import log_validation_failure
from .question_constants import MAX_QUESTION_LENGTH
from ..models.question_schema import validate_question_schema


# ============================================================================
# CONSTANTS
# ============================================================================

STOP_WORDS: Set[str] = {
    'the', 'this', 'that', 'these', 'those', 'a', 'an',
    'of', 'for', 'with', 'without', 'from', 'to', 'by',
    'on', 'at', 'in', 'into', 'through', 'during', 'which',
    'what', 'how', 'why', 'when', 'where', 'who', 'whom'
}

INVALID_CONCEPT_WORDS: Set[str] = {
    'allows', 'provides', 'enables', 'stores', 'manages', 'reduces', 'improves',
    'uses', 'supports', 'offers', 'helps', 'contains', 'includes', 'does', 'doing',
    'responsible', 'processing', 'maintaining', 'organizing', 'allow', 'provide',
    'enable', 'store', 'manage', 'reduce', 'improve', 'use', 'support', 'offer',
    'help', 'contain', 'include', 'do', 'concept', 'example', 'method', 'approach',
    'technique', 'process', 'system', 'layer', 'type', 'category', 'classification',
    'service', 'platform', 'solution', 'resource', 'infrastructure', 'component',
    'module', 'thing', 'item', 'element', 'part', 'way', 'means', 'mechanism'
}

# Generic terms that can appear naturally in questions without causing ambiguity
GENERIC_TERMS: Set[str] = {
    "cloud storage", "cloud storage technology", "cloud computing",
    "cloud computing technology", "data storage", "database",
    "database system", "technology", "system", "storage", "compute",
    "network", "security", "management", "platform", "service",
    "application", "server", "client", "block storage", "file storage",
    "object storage", "software", "hardware", "infrastructure"
}

# Bad distractor patterns to reject
BAD_DISTRACTOR_PATTERNS: List[str] = [
    "distractor option", "option 1", "option 2", "option 3", "option 4",
    "incorrect answer", "wrong choice", "none of these", "none of the above",
    "unknown option", "placeholder", "dummy option"
]

# Banned fill-in-the-blank patterns
BANNED_FILL_BLANK_PATTERNS: List[str] = [
    "what term describes", "known as", "what is this",
    "identify the", "which term", "refers to"
]


# ============================================================================
# TEXT NORMALIZATION HELPERS
# ============================================================================

def _normalize_text(text: str) -> str:
    """Normalize text: lowercase, remove punctuation, collapse spaces."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _extract_meaningful_words(text: str) -> List[str]:
    """Extract meaningful words excluding stop words and short words."""
    words = _normalize_text(text).split()
    return [w for w in words if len(w) > 2 and w not in STOP_WORDS]


def _normalize_question_text(text: str) -> str:
    """Normalize question text for duplicate detection."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    filler_phrases = ['what is', 'which of the following', 'which one', 'the question']
    for phrase in filler_phrases:
        if text.startswith(phrase):
            text = text[len(phrase):].strip()
    return text


def _calculate_overlap(source: Set[str], target: Set[str]) -> float:
    """
    Calculate how much of source is covered by target.

    Used for grounding checks.
    """

    if not source or not target:
        return 0.0

    return len(source & target) / len(source)


# ============================================================================
# CONCEPT ALIASES (Safe Fallback)
# ============================================================================

CONCEPT_ALIASES: Dict[str, Set[str]] = {
    "containerization": {"container", "containers", "container-based"},
    "block storage": {"block", "blocks", "fixed-size blocks"},
    "object storage": {"object", "objects", "object-based"},
    "file storage": {"file", "files", "file-based"},
    "relational database": {"relational", "rdbms", "sql database"},
    "nosql database": {"nosql", "non-relational", "document store"},
    "load balancing": {"load balancer", "load balancing", "lb"},
    "autoscaling": {"auto scaling", "scale out", "scale in"},
    "microservices": {"microservice", "micro-service"},
    "serverless": {"serverless computing", "faas", "function as a service"},
}


# ============================================================================
# CACHE VALIDATION CHECKPOINT
# ============================================================================

def is_valid_question(question: Dict[str, Any]) -> bool:
    """Validate a question for caching and usage."""
    if not question or not isinstance(question, dict):
        print("FAILED: invalid dict")
        return False

    if not validate_question_schema(question):
        print("FAILED: validate_question_schema")
        return False

    required_grounding = ["correct_text", "supporting_fact", "source_note", "fact_id"]
    for field in required_grounding:
        if field not in question or not question[field]:
            return False

    supporting_fact = str(question.get("supporting_fact", ""))
    if not supporting_fact or len(supporting_fact.split()) < 3:
        return False

    invalid_markers = ["#", "[[", "]]", "---", "http", "https"]
    for marker in invalid_markers:
        if marker in supporting_fact:
            return False

    explanation = question.get("explanation", "")
    if not explanation or len(explanation.split()) < 2:
        return False

    question_type = question.get("type", "mcq")

    if question_type == "fill_blank":
        correct_text = question.get("correct_text") or question.get("correct")
        return bool(correct_text)

    correct_letter = question.get("correct", "")
    options = question.get("options", [])

    if not correct_letter:
        return False

    correct_text = get_correct_text_from_options(options, correct_letter)
    if not correct_text:
        return False

    for opt in options:
        if not opt or not extract_option_text(opt):
            return False

    return True


# ============================================================================
# EXPLANATION GROUNDING
# ============================================================================

def has_grounded_explanation(question: Dict[str, Any]) -> bool:
    """Check if explanation is grounded in supporting fact."""
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


# ============================================================================
# DISTRACTOR VALIDATION
# ============================================================================

def validate_distractors(question: dict) -> bool:
    """Reject placeholder distractors generated by LLM."""
    for option in question.get("options", []):
        text = extract_option_text(option).lower()
        for bad in BAD_DISTRACTOR_PATTERNS:
            if bad in text:
                log_validation_failure(
                    question, "distractor", f"Placeholder distractor detected: {text}"
                )
                return False
    return True


# ============================================================================
# STRUCTURE VALIDATION
# ============================================================================

def validate_structure(question: dict) -> bool:
    """Validate required fields, options count, and question formatting."""
    is_fill_blank = "options" not in question

    required = ["question", "correct", "explanation"]
    if not is_fill_blank:
        required.append("options")

    missing = [field for field in required if field not in question]
    if missing:
        log_validation_failure(
            question, "structure", f"Missing required fields: {missing}"
        )
        return False

    if not is_fill_blank:
        if not isinstance(question["options"], list) or len(question["options"]) != 4:
            log_validation_failure(
                question, "structure", "Options must contain exactly 4 items"
            )
            return False

    q_text = question["question"].strip()

    if q_text and not q_text.endswith("?"):
        q_text = q_text.rstrip(".!,:;") + "?"
        question["question"] = q_text

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


# ============================================================================
# ANSWER NORMALIZATION
# ============================================================================

def normalize_and_validate_correct_field(question: dict) -> bool:
    """Convert different answer formats into standard format."""
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

    log_validation_failure(question, "correct_field", "Unable to resolve correct answer")
    return False


# ============================================================================
# CONCEPT ALIGNMENT VALIDATION
# ============================================================================

def validate_question_focus(
    question: dict,
    concept: str,
    supporting_fact: str = ""
) -> bool:
    """
    Validate that the generated question focuses on the correct concept.
    Priority: Exact match > Alias match > Semantic overlap > Word overlap.
    """
    q_text = question.get("question", "")
    q_normalized = _normalize_text(q_text)
    concept_normalized = _normalize_text(concept)
    concept_lower = concept.lower()

    # Reject if question uses "layer" incorrectly
    if "layer" in q_text.lower() and "layer" not in concept_lower:
        log_validation_failure(
            question, "focus", f"Question uses 'layer' but concept is '{concept}'"
        )
        return False

    # Priority 1: Exact concept match
    if concept_normalized in q_normalized:
        return True

    compact_question = q_normalized.replace(" ", "")
    compact_concept = concept_normalized.replace(" ", "")
    if compact_concept in compact_question:
        return True

    # Priority 2: Alias matching
    concept_key = concept_normalized.lower()
    aliases = CONCEPT_ALIASES.get(concept_key, set())
    for alias in aliases:
        alias_normalized = _normalize_text(alias)
        if alias_normalized in q_normalized:
            return True
        if alias_normalized.replace(" ", "") in compact_question:
            return True

    # Priority 3: Supporting fact semantic overlap
    if supporting_fact:

        fact_words = set(_extract_meaningful_words(supporting_fact))
        q_words = set(_extract_meaningful_words(q_text))

        matched_words = fact_words & q_words

        if fact_words and q_words:

            # Measure how much of the supporting fact
            # is represented in the question.
            fact_coverage = len(matched_words) / len(fact_words)

            # Accept strong definition matches.
            if fact_coverage >= 0.25 and len(matched_words) >= 3:
                return True

    # Priority 4: Concept word overlap (fallback)
    concept_words = set(_extract_meaningful_words(concept))
    q_words = set(_extract_meaningful_words(q_text))

    if concept_words and q_words:
        overlap = _calculate_overlap(concept_words, q_words)
        if overlap >= 0.40:
            return True

    log_validation_failure(
        question, "focus", f"Question doesn't reference concept '{concept}'"
    )
    return False


# ============================================================================
# TOPIC RELEVANCE VALIDATION
# ============================================================================

def is_relevant_to_topic(
    question: str,
    topic: str,
    answer: str = "",
    supporting_fact: str = "",
    fact_topic: str = "",
    concept: str = "",
) -> bool:
    """
    Validate that a generated question is grounded in its supporting fact
    and belongs to the requested topic.

    The validator does NOT infer relationships or maintain concept knowledge.
    It only verifies:
    1. fact_topic matches the requested topic
    2. Answer is grounded in supporting_fact
    3. Question describes the supporting_fact

    Pass conditions:
    - fact_topic == topic (exact match)
    - Answer appears in or is strongly represented by supporting_fact
    - Question describes content from supporting_fact

    Fail conditions:
    - fact_topic != topic
    - Answer is not grounded in supporting_fact
    - Question describes concepts not in supporting_fact
    """
    if not topic:
        return True

    # ==========================================
    # Validation 1: fact_topic must match requested topic
    # ==========================================
    if fact_topic:
        if fact_topic.lower() != topic.lower():
            log_validation_failure(
                None,
                "topic_relevance",
                f"fact_topic '{fact_topic}' does not match requested topic '{topic}'"
            )
            return False
    else:
        # If fact_topic is missing, fall back to direct topic verification
        # This ensures backward compatibility with existing facts
        if supporting_fact:
            fact_lower = supporting_fact.lower()
            topic_words = [w for w in topic.lower().split() if len(w) > 3]
            if not any(word in fact_lower for word in topic_words):
                log_validation_failure(
                    None,
                    "topic_relevance",
                    f"No fact_topic provided and topic '{topic}' not found in supporting fact"
                )
                return False
        else:
            # No fact_topic and no supporting_fact - can't validate
            log_validation_failure(
                None,
                "topic_relevance",
                "Cannot validate: no fact_topic and no supporting_fact"
            )
            return False

    # ==========================================
    # Helper: Extract meaningful words
    # ==========================================
    def _get_words(text: str) -> Set[str]:
        if not text:
            return set()
        words = _extract_meaningful_words(text)
        return set(words)

    def _overlap(set_a: Set[str], set_b: Set[str]) -> float:
        if not set_a or not set_b:
            return 0.0
        return len(set_a & set_b) / len(set_a)

    # ==========================================
    # Validation 2: Answer must be grounded in supporting_fact
    # ==========================================
    if answer and supporting_fact:
        answer_lower = answer.lower()
        fact_lower = supporting_fact.lower()

        # Direct match: answer appears in fact
        if answer_lower in fact_lower:
            pass  # Grounded
        else:
            # Check word overlap
            answer_words = _get_words(answer)
            fact_words = _get_words(supporting_fact)

            if answer_words and fact_words:
                coverage = _overlap(answer_words, fact_words)
                if coverage < 0.15 and len(answer_words & fact_words) < 2:

                    # Allow concept grounding or root/stem word overlap
                    # Example:
                    # concept = "Containerization"
                    # fact = "packages applications into isolated containers"
                    has_stem_match = any(
                        ans[:5] in word or word[:5] in ans
                        for ans in (answer_words | _get_words(concept))
                        for word in fact_words
                        if len(ans) >= 4 and len(word) >= 4
                    )
                    if (concept and concept.lower() in supporting_fact.lower()) or has_stem_match:
                        pass
                    else:
                        log_validation_failure(
                            None,
                            "topic_relevance",
                            f"Answer '{answer}' not grounded in supporting fact"
                        )
                        return False
            else:
                log_validation_failure(
                    None,
                    "topic_relevance",
                    f"Answer '{answer}' not found in supporting fact"
                )
                return False

    # ==========================================
    # Validation 3: Question must describe supporting_fact
    # ==========================================
    if question and supporting_fact:
        question_words = _get_words(question)
        fact_words = _get_words(supporting_fact)

        if question_words and fact_words:
            question_grounding = _overlap(question_words, fact_words)

            if question_grounding < 0.10 and len(question_words & fact_words) < 2:
                log_validation_failure(
                    None,
                    "topic_relevance",
                    "Question not grounded in supporting fact"
                )
                return False

    # ==========================================
    # All validations passed
    # ==========================================
    return True


# ============================================================================
# DUPLICATE DETECTION
# ============================================================================

def is_duplicate_question(
    new_question: str, existing_questions: List[str], threshold: float = 0.85
) -> bool:
    """Check if a question is a duplicate of existing questions."""
    if not new_question or not existing_questions:
        return False

    new_normalized = _normalize_question_text(new_question)
    if not new_normalized:
        return False

    for old_question in existing_questions:
        if not old_question:
            continue

        old_normalized = _normalize_question_text(old_question)
        if not old_normalized:
            continue

        similarity = SequenceMatcher(None, new_normalized, old_normalized).ratio()
        if similarity >= threshold:
            print(f"⚠️ Duplicate question detected (similarity: {similarity:.2f})")
            return True

    return False


# ============================================================================
# CONCEPT QUALITY VALIDATION
# ============================================================================

def is_valid_concept(concept: str) -> bool:
    """Check if a concept is valid for fallback generation."""
    if not concept:
        return False

    concept_clean = concept.strip()
    if not concept_clean:
        return False

    concept_lower = concept_clean.lower()
    words = concept_lower.split()

    # Single word concepts
    if len(words) == 1:
        # Allow acronyms (2+ uppercase letters)
        if concept_clean.isupper() and len(concept_clean) >= 2:
            return True

        # Reject invalid concept words
        if concept_lower in INVALID_CONCEPT_WORDS:
            return False

        # Reject very short generic words
        if len(concept_lower) < 4:
            return False

        # Reject common generic single words
        if concept_lower in {'system', 'method', 'process', 'service', 'platform'}:
            return False

        return True

    # Multi-word concepts
    if len(words) >= 2:
        # Reject generic phrases
        generic_phrases = [
            'allows for', 'provides a', 'enables the', 'uses a', 'supports the',
            'method of', 'process of', 'system for', 'type of', 'category of'
        ]
        for phrase in generic_phrases:
            if phrase in concept_lower:
                return False

        # Allow common multi-word technical terms even if ending with generic words
        generic_endings = {'system','service','database','platform','storage','network'}
        allowed_generic_concepts = {"operating system","distributed system","relational database","cloud database","database system","container platform",}
        if words[-1] in generic_endings:
            # Allow if it's a specific multi-word concept (e.g., "Operating System")
            if len(words) >= 2 and words[0] not in ['abstract', 'generic', 'basic', 'simple']:
                return True
            return False

        return True

    # Capitalized word
    if concept_clean[0].isupper() and len(concept_clean) > 2:
        return True

    return False


# ============================================================================
# QUESTION AMBIGUITY VALIDATION
# ============================================================================

def validate_question_uniqueness(question: dict) -> bool:
    """Reject questions where a distractor is described by the question."""
    question_text = question.get("question", "").lower()
    question_type = question.get("type", "mcq")

    if question_type == "fill_blank":
        return validate_fill_blank_question(question)

    options = question.get("options", [])
    correct_letter = question.get("correct", "")

    correct = get_correct_text_from_options(options, correct_letter).lower()
    if not correct:
        return False

    question_words = set(_extract_meaningful_words(question_text))
    supporting_fact = question.get("supporting_fact", "").lower()
    fact_words = set(_extract_meaningful_words(supporting_fact)) if supporting_fact else set()

    for option in options:

        option_text = extract_option_text(option).lower()

        if option_text == correct:
            continue

        option_words = set(_extract_meaningful_words(option_text))
        if not option_words:
            continue

        # Check if question mentions distractor (ignore generic terms)
        option_key = option_text.strip()
        if option_key in question_text and option_key not in GENERIC_TERMS:
            log_validation_failure(
                question,
                "ambiguity",
                f"Question mentions distractor '{option_key}'"
            )
            return False

        # Check if question could describe distractor (word overlap)
        if option_words:
            overlap = _calculate_overlap(question_words, option_words)
            if overlap >= 0.80 and option_key not in GENERIC_TERMS:
                # Verify it's not a generic term
                if option_key not in GENERIC_TERMS:
                    log_validation_failure(
                        question,
                        "ambiguity",
                        f"Question could also describe '{option_key}'"
                    )
                    return False

        # Check if distractor matches supporting fact more than correct answer
        if supporting_fact and fact_words:
            correct_fact_overlap = _calculate_overlap(fact_words, question_words)
            option_fact_overlap = _calculate_overlap(fact_words, option_words)

            if option_fact_overlap > correct_fact_overlap and option_fact_overlap >= 0.35:
                log_validation_failure(
                    question,
                    "ambiguity",
                    f"Question wording overlaps distractor concept '{option_key}'"
                )
                return False

    return True


# ============================================================================
# FILL BLANK VALIDATION
# ============================================================================

def validate_fill_blank_question(question: dict) -> bool:
    """Validate fill-in-the-blank questions."""
    text = question.get("question", "")
    correct = question.get("correct", "").strip()

    if not text or not correct:
        return False

    if text.count("_______") != 1:
        log_validation_failure(question, "fill_blank", "Must contain exactly one blank")
        return False

    # Full answer should not appear in question
    if correct.lower() in text.lower():
        log_validation_failure(question, "fill_blank", "Answer appears inside question")
        return False

    # Multi-word answer: ensure not exposed
    answer_words = correct.lower().split()
    question_text = text.lower()

    if len(answer_words) >= 2:
        matched_words = sum(1 for word in answer_words if word in question_text)
        if matched_words >= len(answer_words) - 1:
            log_validation_failure(
                question,
                "fill_blank",
                "Most answer words already appear in question"
            )
            return False

    # Reject weak patterns
    lower = text.lower()
    for pattern in BANNED_FILL_BLANK_PATTERNS:
        if pattern in lower:
            log_validation_failure(question, "fill_blank", f"Contains banned pattern: {pattern}")
            return False

    return True