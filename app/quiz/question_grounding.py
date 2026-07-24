import logging
import re

from typing import Any, Dict
from .text_normalizer import normalize_supporting_fact

from .options_parser import (
    extract_option_text,
    get_correct_text_from_options,
)

from .question_constants import (
    MAX_SUPPORTING_WORDS,
    STOP_WORDS,
)

from .question_explanation import build_consistent_explanation
from .validation_logger import log_validation_failure

logger = logging.getLogger(__name__)


def validate_grounding(
    question: Dict[str, Any], context: str, supporting_fact: str = ""
) -> bool:
    """
    Check if the correct answer is grounded in the note-backed context.
    Uses flexible matching: exact, keyword, and phrase-level.
    """
    if "correct" not in question or "options" not in question:
        return False

    correct_letter = question["correct"]
    options = question["options"]
    correct_text = get_correct_text_from_options(options, correct_letter)

    if not correct_text:
        log_validation_failure(
            question,
            "grounding",
            "Could not extract correct text from options",
            {"correct_letter": correct_letter},
        )
        return False

    # Prefer supporting_fact, fallback to context
    grounding_context = f"{supporting_fact}\n{context}"
    if not grounding_context:
        log_validation_failure(
            question, "grounding", "No context provided for grounding check"
        )
        return False

    context_lower = grounding_context.lower()
    correct_lower = correct_text.lower()
    correct_words = correct_lower.split()

    # Normalize common concept variations
    concept_aliases = {
        "containerization": [
            "container",
            "containers",
            "application dependencies",
            "run consistently",
            "package applications"
        ],
        "cloud computing": [
            "computing services",
            "storage",
            "databases",
            "software",
            "internet"
        ],
    }

    # Level 1: Exact answer appears
    if correct_lower in context_lower:
        logger.debug("Grounding exact match: %s", correct_text)
        return True

    # Level 2: Supporting fact strongly describes the concept
    meaningful_words = [
        word
        for word in correct_words
        if len(word) > 3 and word not in STOP_WORDS
    ]

    # Add concept alias keywords
    aliases = concept_aliases.get(correct_lower, [])

    if aliases:
        meaningful_words.extend(
            [word.lower() for word in aliases]
        )

    matched = [
        word
        for word in meaningful_words
        if word in context_lower
    ]

    # Accept either:
    # 1. Most answer keywords appear
    # 2. The supporting fact is reasonably descriptive

    if meaningful_words:

        overlap = len(matched) / len(meaningful_words)

        if overlap >= 0.50:
            logger.debug(
                "Grounding keyword overlap %.2f",
                overlap,
            )
            return True

    # Description fallback:
    # Accept only if answer concept appears in the supporting fact.
    if correct_lower in context_lower:
        return True

    # Level 3: Multi-word phrase matching (at least 60% of words appear together)
    if len(correct_words) >= 2:
        sentences = re.split(r"[.!?\n]", context_lower)

        meaningful_correct_words = [
            w for w in correct_words if w not in STOP_WORDS and len(w) > 3
        ]

        if len(meaningful_correct_words) >= 2:
            for sentence in sentences:
                sentence_words = {
                    w.lower()
                    for w in re.findall(r"\w+", sentence)
                }

                matched_words = [
                    w for w in meaningful_correct_words if w in sentence_words
                ]

                overlap = len(matched_words) / len(meaningful_correct_words)

                if overlap >= 0.50:
                    return True

    log_validation_failure(
        question,
        "grounding",
        "Correct answer not found in context",
        {
            "correct_text": correct_text,
            "context_preview": grounding_context[:100] + "...",
            "correct_words": correct_words[:3],
        },
    )
    return False

def explanation_supported_by_fact(
    explanation: str,
    supporting_fact: str,
    correct_text: str,
) -> bool:
    """
    Returns True if the explanation is actually supported by the note-backed fact.
    """

    if not explanation or not supporting_fact:
        return False

    explanation = explanation.lower()
    fact = supporting_fact.lower()
    correct = correct_text.lower()

    # Explanation should mention the correct concept.
    if correct not in explanation:
        return False

    fact_words = {
        w for w in re.findall(r"\w+", fact)
        if len(w) > 3 and w not in STOP_WORDS
    }

    explanation_words = {
        w for w in re.findall(r"\w+", explanation)
        if len(w) > 3 and w not in STOP_WORDS
    }

    if not fact_words:
        return False

    overlap = len(fact_words & explanation_words) / len(fact_words)

    return overlap >= 0.30

def is_valid_explanation(
    explanation: str,
    correct_text: str,
) -> bool:
    """
    Reject explanations that are just copied facts.
    """

    if not explanation:
        return False

    text = explanation.lower()

    # Must mention answer
    if correct_text.lower() not in text:
        return False

    # Reject raw fact formatting
    banned_patterns = [
        " refers to ",
        " is a ",
        " is an ",
        " – ",
        " - ",
    ]

    fact_like_count = sum(
        1 for pattern in banned_patterns
        if pattern in text
    )

    # Too many definition markers means it copied the fact
    if fact_like_count >= 3:
        logger.warning(
            "Explanation looks like copied fact: %s",
            explanation[:100],
        )
        return False

    return True

def attach_grounding_fields(
    question: Dict[str, Any], correct_text: str, supporting_fact: str, context: str = ""
) -> bool:
    """Attach correct_text/supporting_fact/explanation to a question."""
    if not question or not isinstance(question, dict):
        return False
    
    question["correct_text"] = correct_text or ""
    question["concept"] = correct_text
    question["concept_type"] = question.get("concept_type") or "concept"
    question["supporting_fact"] = normalize_supporting_fact(
        supporting_fact or ""
    )

    # Keep full supporting fact for explanation generation
    if len(question["supporting_fact"].split()) > MAX_SUPPORTING_WORDS:
        question["supporting_fact"] = " ".join(
            question["supporting_fact"].split()[:MAX_SUPPORTING_WORDS]
        )
    question["fact_id"] = (
    question.get("fact_id")
        or f"fact_{abs(hash(question['supporting_fact']))}"
    )

    question["source_note"] = (
        question.get("source_note")
        or "fact_cache"
    )
    logger.debug(
        "Attached supporting fact: %s",
        question["supporting_fact"][:120]
    )

    if not question["supporting_fact"]:
        logger.debug(
            "Supporting fact missing. Falling back to context."
        )

        question["supporting_fact"] = normalize_supporting_fact(context)

        if not question["supporting_fact"]:
            logger.debug(
                "Context fallback also failed."
            )
            return False


    # Ignore LLM-generated explanations.
    # Explanations must always be generated from supporting FACT.
    question["explanation"] = ""

    # Fill blank questions use the supporting fact for explanation.
    if question.get("type") == "fill_blank":
        print("TYPE CHECK:", repr(question.get("type")))
        print("CORRECT TEXT:", repr(correct_text))
        print("SUPPORTING FACT LENGTH:", len(question.get("supporting_fact", "")))

        if correct_text and question["supporting_fact"]:
            question["explanation"] = build_consistent_explanation(
                question_text=question.get("question", ""),
                options=question.get("options", []),
                correct_letter=question.get("correct", ""),
                correct_text=correct_text,
                context=question["supporting_fact"],
                facts=[
                    {
                        "supporting_fact": question["supporting_fact"]
                    }
                ],
            )

        return True
    
    # Generate grounded explanation from FACT only.
    if correct_text and question["supporting_fact"]:

        explanation = build_consistent_explanation(
            question_text=question.get("question", ""),
            options=question.get("options", []),
            correct_letter=question.get("correct", ""),
            correct_text=correct_text,
            context=question["supporting_fact"],
            facts=[
                {
                    "supporting_fact": question["supporting_fact"]
                }
            ],
        )

        if explanation:
            question["explanation"] = explanation
            return True

    # Final safe fallback.
    if correct_text and question["supporting_fact"]:
        question["explanation"] = (
            f"{correct_text} is supported by the provided fact."
        )
        return True

    
    elif correct_text:
        question["explanation"] = f"{correct_text} is the correct answer."
        return True

    question["explanation"] = ""
    return True

def question_equals_answer(question_text: str, options: list) -> bool:
    """Check if the question is just restating the correct answer."""
    q_clean = question_text.strip().lower().rstrip(".?")
    for opt in options:
        opt_text = extract_option_text(opt).lower().rstrip(".")
        if (
            opt_text
            and (opt_text in q_clean or q_clean in opt_text)
            and len(opt_text) > 20
        ):
            logger.warning("Question restates answer: '%s...'", opt_text[:40])
            return True
    return False
