import logging
import re

from typing import Any, Dict, Optional

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



def validate_grounding(question: Dict[str, Any], context: str, supporting_fact: str = "") -> bool:
    """
    Check if the correct answer is grounded in the note-backed context.
    Uses flexible matching: exact, keyword, and phrase-level.
    """
    if 'correct' not in question or 'options' not in question:
        return False
    
    correct_letter = question['correct']
    options = question['options']
    correct_text = get_correct_text_from_options(options, correct_letter)
    
    if not correct_text:
        log_validation_failure(question, "grounding", "Could not extract correct text from options", {"correct_letter": correct_letter})
        return False
    
    # Prefer supporting_fact, fallback to context
    grounding_context = supporting_fact or context or ""
    if not grounding_context:
        log_validation_failure(question, "grounding", "No context provided for grounding check")
        return False

    context_lower = grounding_context.lower()
    correct_lower = correct_text.lower()
    correct_words = correct_lower.split()
    
    # Level 1: Exact match
    if correct_lower in context_lower:
        logger.debug(f"Grounding exact match: {correct_text}")
        return True
    
    # Level 2: Any significant word appears in context
    for word in correct_words:
        if len(word) > 3 and word not in STOP_WORDS:
            if word in context_lower:
                logger.debug(f"Grounding keyword match: '{word}' from '{correct_text}'")
                return True
    
    # Level 3: Multi-word phrase matching (at least 60% of words appear together)
    if len(correct_words) >= 2:
        sentences = re.split(r'[.!?\n]', context_lower)
        for sentence in sentences:
            sentence_words = set(sentence.split())
            matched_words = [w for w in correct_words if w in sentence_words]
            if len(matched_words) >= len(correct_words) * 0.6:
                logger.debug(f"Grounding phrase match: {correct_text}")
                return True
    
    log_validation_failure(question, "grounding", "Correct answer not found in context", {
        "correct_text": correct_text,
        "context_preview": grounding_context[:100] + "...",
        "correct_words": correct_words[:3]
    })
    return False



def normalize_supporting_fact(text: str) -> str:
    """Turn a raw note fragment into a short atomic supporting fact."""
    if not text:
        return ""

    cleaned = str(text).strip()
    cleaned = re.sub(r'^\s*#+\s*', '', cleaned)
    cleaned = re.sub(r'^\s*[-*+]\s*', '', cleaned)
    cleaned = re.sub(r'^\s*\d+\.\s*', '', cleaned)
    cleaned = re.sub(r'\[\[(.*?)\]\]', r'\1', cleaned)
    cleaned = re.sub(r'[*_`>#]', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    cleaned = cleaned.rstrip(' .')

    if not cleaned:
        return ""
    if any(marker in cleaned.lower() for marker in ['#', '[[', ']]', '---', 'http', 'https']):
        return ""
    if len(cleaned.split()) > MAX_SUPPORTING_WORDS:
        cleaned = ' '.join(cleaned.split()[:MAX_SUPPORTING_WORDS]).rstrip(' .')
    if cleaned.lower().startswith(('how ', 'why ', 'what ', 'when ', 'where ',
                                    'conclusion', 'summary', 'overview', 'references')):
        return ""
    return cleaned



def attach_grounding_fields(question: Dict[str, Any], correct_text: str, supporting_fact: str, context: str = "") -> bool:
    """Attach correct_text/supporting_fact/explanation to a question."""
    if not question or not isinstance(question, dict):
        return False

    question['correct_text'] = correct_text or ""
    question['supporting_fact'] = normalize_supporting_fact(supporting_fact or "")

    if not question['supporting_fact']:
        question['supporting_fact'] = normalize_supporting_fact(context or "")

    # Try to build a proper explanation
    if correct_text and question['supporting_fact']:
        explanation = build_consistent_explanation(
            question_text=question.get('question', ''),
            options=question.get('options', []),
            correct_letter=question.get('correct', ''),
            correct_text=correct_text,
            context=question['supporting_fact'],
            facts=[{'supporting_fact': question['supporting_fact']}]
        )
        if explanation and not question.get('explanation'):
            question['explanation'] = explanation
        return True
    
    # Fallback: create a simple grounded explanation
    if correct_text and question['supporting_fact']:
        question['explanation'] = f"{correct_text} is correct because {question['supporting_fact']}"
        return True
    elif correct_text:
        question['explanation'] = f"{correct_text} is the correct answer."
        return True
    
    question['explanation'] = ""
    return True



def select_supporting_fact(correct_text: str, supporting_facts: Optional[list] = None,
                            fallback_context: str = "") -> str:
    """Pick the strongest note-backed supporting sentence for a question."""

    candidates = []

    if supporting_facts:
        for fact in supporting_facts:
            if isinstance(fact, dict):
                candidate = (
                    fact.get('supporting_fact')
                    or fact.get('sentence')
                    or fact.get('definition')
                    or ""
                )
            else:
                candidate = str(fact)

            cleaned = normalize_supporting_fact(candidate)

            if cleaned:
                candidates.append(cleaned)

    if fallback_context:
        sentences = re.split(r'[.!?\n]+', fallback_context)

        for sentence in sentences:
            cleaned = normalize_supporting_fact(sentence)

            if cleaned:
                candidates.append(cleaned)


    if not candidates:
        return ""


    correct_words = [
        w.lower()
        for w in re.findall(r'\w+', correct_text)
        if len(w) > 2
    ]


    best_candidate = ""
    best_score = 0


    for candidate in candidates:

        candidate_lower = candidate.lower()

        score = 0

        for word in correct_words:
            if word in candidate_lower:
                score += 1


        if correct_text.lower() in candidate_lower:
            score += 5


        if score > best_score:
            best_score = score
            best_candidate = candidate


    return best_candidate or candidates[0]


def question_equals_answer(question_text: str, options: list) -> bool:
    """Check if the question is just restating the correct answer."""
    q_clean = question_text.strip().lower().rstrip('.?')
    for opt in options:
        opt_text = extract_option_text(opt).lower().rstrip('.')
        if opt_text and (opt_text in q_clean or q_clean in opt_text) and len(opt_text) > 20:
            logger.warning(
                "Question restates answer: '%s...'",
                opt_text[:40]
            )
            return True
    return False