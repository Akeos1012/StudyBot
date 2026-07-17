"""
Fallback question generation utilities.

Used when LLM-generated questions fail validation.
Creates safe fact-based fallback questions from extracted concepts.
"""

import re
from typing import Optional

from .question_grounding import normalize_supporting_fact
from .question_constants import MIN_SUPPORTING_WORDS

# Generic words that should not become quiz answers
INVALID_CONCEPT_WORDS = {
    "allows",
    "provides",
    "enables",
    "stores",
    "manages",
    "reduces",
    "improves",
    "uses",
    "supports",
    "offers",
    "helps",
    "contains",
    "includes",
    "does",
    "doing",
    "responsible",
    "processing",
    "maintaining",
    "organizing",
    "allow",
    "provide",
    "enable",
    "store",
    "manage",
    "reduce",
    "improve",
    "use",
    "support",
    "offer",
    "help",
    "contain",
    "include",
    "do",
    "concept",
    "example",
    "method",
    "approach",
    "technique",
    "process",
    "system",
    "layer",
    "type",
    "category",
    "classification",
    "service",
    "platform",
    "solution",
    "resource",
    "infrastructure",
    "component",
    "module",
}


def create_fact_based_question(
    concept: str,
    supporting_fact: str,
    topic: str,
    source_note: str = "",
    fact_id: str = "",
) -> dict:
    """
    Create a fallback question directly from extracted facts.
    """

    supporting_fact = normalize_supporting_fact(supporting_fact)

    if not supporting_fact:
        supporting_fact = f"Provides information about {concept}."

    fact_clean = supporting_fact

    if concept.lower() in fact_clean.lower():

        fact_clean = re.sub(
            re.escape(concept), "_______", fact_clean, flags=re.IGNORECASE
        )

        question_text = f"Which term completes this statement: {fact_clean}?"

    else:

        question_text = f"What is the correct term for: {supporting_fact}?"

    return {
        "question": question_text,
        "options": [
            f"A) {concept}",
            "B) Related Technology",
            "C) Alternative Approach",
            "D) Different Concept",
        ],
        "correct": "A",
        "correct_text": concept,
        "supporting_fact": supporting_fact,
        "explanation": (f"{supporting_fact}"),
        "source_note": (
            source_note or "fact_based_fallback"
        ),

        "fact_id": (
            fact_id
            or f"fact_fallback_{concept.lower().replace(' ', '_')}"
        ),
        "_is_fallback": True,
        "_quality_score": 0.7,
        "_quality_scores": {
            "semantic_coherence": 1.0,
            "distractor_plausibility": 0.5,
            "type_consistency": 1.0,
        },
    }


def generate_fallback_question(
    context: str,
    topic: str,
    extracted_concepts: list = None,
    supporting_facts: list = None,
) -> Optional[dict]:
    """
    Generate fallback question using available concepts.
    """

    # 1. Use extracted concepts first
    if extracted_concepts:

        for concept in extracted_concepts:

            if concept and is_valid_concept(concept):

                supporting_fact = find_supporting_fact_for_concept(concept, context)

                if supporting_fact:

                    return create_fact_based_question(concept, supporting_fact, topic)

    # 2. Use cached supporting facts
    if supporting_facts:

        for sf in supporting_facts:

            if isinstance(sf, dict):

                concept = (
                    sf.get("concept") or sf.get("correct_text") or sf.get("answer")
                )

                supporting_fact = (
                    sf.get("supporting_fact")
                    or sf.get("statement")
                    or sf.get("definition")
                )

                if concept and is_valid_concept(concept) and supporting_fact:

                    return create_fact_based_question(
                        concept=concept,
                        supporting_fact=supporting_fact,
                        topic=topic,
                        source_note=sf.get("source_note", ""),
                        fact_id=sf.get("fact_id", ""),
                    )

    # 3. Extract capitalized concepts from context

    context_concepts = re.findall(
        r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,3})\b", context
    )

    for concept in context_concepts:

        if is_valid_concept(concept):

            supporting_fact = find_supporting_fact_for_concept(concept, context)

            if supporting_fact:

                return create_fact_based_question(concept, supporting_fact, topic)

    # 4. Use topic as final concept

    if topic and is_valid_concept(topic):

        return create_fact_based_question(topic, context[:200] + "...", topic)

    return None


def generate_generic_fallback(context: str, topic: str) -> dict:
    """
    Last resort fallback when no concepts exist.
    """

    return {
        "question": (f"What is the main concept discussed in {topic}?"),
        "options": [
            "A) The Main Concept",
            "B) Related Technology",
            "C) Alternative Approach",
            "D) Different Concept",
        ],
        "correct": "A",
        "correct_text": "The Main Concept",
        "supporting_fact": (context[:200] + "..."),
        "explanation": (
            "The main concept is the correct answer " "based on the content."
        ),
        "source_note": "generic_fallback",
        "fact_id": (f"generic_fallback_{topic.lower().replace(' ', '_')}"),
        "_is_fallback": True,
        "_quality_score": 0.5,
        "_quality_scores": {
            "semantic_coherence": 0.5,
            "distractor_plausibility": 0.3,
            "type_consistency": 0.7,
        },
    }


def is_valid_concept(concept: str) -> bool:
    """
    Check if a concept is suitable as a quiz answer.
    """

    if not concept or len(concept) < 2:
        return False

    concept_lower = concept.lower()

    if concept_lower in INVALID_CONCEPT_WORDS:
        return False

    if len(concept_lower) == 1:
        return False

    # Allow multi-word concepts
    if len(concept.split()) >= 2:
        return True

    # Reject broad categories
    if concept_lower in ["database", "cloud", "algorithm", "programming"]:
        return False

    # Allow named technologies/concepts
    if concept[0].isupper() and len(concept) > 2:
        return True

    return False


def find_supporting_fact_for_concept(concept: str, context: str) -> str:
    """
    Find a sentence that supports the concept.
    """

    if not context or not concept:
        return ""

    sentences = re.split(r"[.!?\n]+", context)

    # Prefer sentences containing the concept

    for sentence in sentences:

        if concept.lower() in sentence.lower():

            cleaned = normalize_supporting_fact(sentence)

            if cleaned and len(cleaned.split()) >= MIN_SUPPORTING_WORDS:
                return cleaned

    # Otherwise use first useful sentence

    for sentence in sentences:

        cleaned = normalize_supporting_fact(sentence)

        if cleaned and len(cleaned.split()) >= MIN_SUPPORTING_WORDS:
            return cleaned

    return context[:200] + "..."
