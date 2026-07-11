"""
Question Builder Module - Assembles questions from facts and distractors.

This module is responsible ONLY for assembling a complete question from:
- A validated fact
- Selected distractors
- Appropriate question type

It does NOT handle:
- Fact normalization or validation
- Distractor selection
- Quality scoring
- Scenario generation
- Template management (moved to question_templates.py)

All facts passed to this module are assumed to be already normalized and validated.
"""

import random
import logging

from typing import List, Dict, Any, Optional, Tuple

from .question_templates import QuestionTemplates
from .distractor_selector import DistractorSelector
from ..models.fact_schema import get_question_types_for_type, get_question_difficulty

logger = logging.getLogger(__name__)


# ============================================================================
# MAIN CLASS
# ============================================================================

class QuestionBuilder:
    """
    Assembles questions from validated facts and distractors.

    This class coordinates the question assembly pipeline:
    1. Select question type based on concept type
    2. Build question text using templates
    3. Assemble options (correct + distractors)
    4. Generate explanation
    5. Return complete question object

    All inputs are assumed to be already validated.
    """

    def __init__(self):
        """Initialize the question builder with required dependencies."""
        self.templates = QuestionTemplates()
        self.distractor_selector = DistractorSelector()
        

        # Question type weights by concept type
        self.type_weights = {
            "algorithm": {
                "definition": 0.25, "comparison": 0.25,
                "application": 0.25, "scenario": 0.15,
                "reverse_definition": 0.10
            },
            "model": {
                "definition": 0.30, "comparison": 0.20,
                "application": 0.25, "scenario": 0.15,
                "reverse_definition": 0.10
            },
            "metric": {
                "definition": 0.35, "comparison": 0.20,
                "application": 0.20, "scenario": 0.10,
                "reverse_definition": 0.15
            },
            "system": {
                "definition": 0.25, "comparison": 0.20,
                "application": 0.30, "scenario": 0.15,
                "reverse_definition": 0.10
            },
            "process": {
                "definition": 0.25, "comparison": 0.15,
                "application": 0.30, "scenario": 0.20,
                "reverse_definition": 0.10
            },
            "concept": {
                "definition": 0.35, "comparison": 0.15,
                "application": 0.20, "scenario": 0.20,
                "reverse_definition": 0.10
            },
            "data_structure": {
                "definition": 0.30, "comparison": 0.20,
                "application": 0.25, "scenario": 0.15,
                "reverse_definition": 0.10
            },
            "framework": {
                "definition": 0.30, "comparison": 0.25,
                "application": 0.25, "scenario": 0.10,
                "reverse_definition": 0.10
            },
        }

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def build_question(self, fact: Dict[str, Any],
                       distractors: List[str]) -> Optional[Dict[str, Any]]:
        """
        Build a complete question from a fact and distractors.

        Args:
            fact: Validated fact dictionary with at minimum:
                  - concept: The main concept
                  - definition: The definition or supporting fact
                  - concept_type: The concept type
                  - topic: The topic name
            distractors: List of distractor concept names

        Returns:
            Complete question dictionary, or None if building fails

        Example:
            >>> builder = QuestionBuilder()
            >>> fact = {
            ...     "concept": "Cloud Storage",
            ...     "definition": "Stores data on remote servers",
            ...     "concept_type": "system",
            ...     "topic": "Cloud"
            ... }
            >>> distractors = ["Local Storage", "Network Storage", "Distributed Storage"]
            >>> question = builder.build_question(fact, distractors)
        """
        if not fact or not distractors:
            logger.warning("Missing fact or distractors for question building")
            return None

        concept = fact.get("concept", "")
        definition = fact.get("definition", "")
        topic = fact.get("topic", "Unknown")
        concept_type = self._get_concept_type(fact)
        supporting_fact = self._get_supporting_fact(fact)

        if not concept or not definition:
            logger.warning("Fact missing concept or definition")
            return None

        # Select question type
        question_type = self._select_question_type(concept_type, distractors)

        # Build question text
        question_text = self._build_question_text(
            question_type=question_type,
            concept=concept,
            definition=definition,
            topic=topic,
            distractors=distractors
        )

        # Build options
        options, correct_letter = self._build_options(concept, distractors)

        # Calculate difficulty
        difficulty = get_question_difficulty(concept_type, question_type)

        # Generate explanation
        explanation = self._build_explanation(
            question_text=question_text,
            options=options,
            correct_letter=correct_letter,
            correct_text=concept,
            supporting_fact=supporting_fact
        )

        return {
            "question": question_text,
            "options": options,
            "correct_letter": correct_letter,
            "correct_answer": concept,
            "explanation": explanation,
            "source": fact.get("source", "Unknown"),
            "difficulty": difficulty,
            "question_type": question_type,
            "concept": concept,
            "concept_type": concept_type,
            "topic": topic,
            "supporting_fact": supporting_fact
        }

    def build_quiz(self, facts: List[Dict[str, Any]],
                   count: int = 3) -> List[Dict[str, Any]]:
        """
        Build a quiz from a list of facts.

        This method selects the best facts and generates questions for them.

        Args:
            facts: List of validated fact dictionaries
            count: Number of questions to generate

        Returns:
            List of complete question dictionaries

        Example:
            >>> builder = QuestionBuilder()
            >>> questions = builder.build_quiz(facts, count=3)
        """
        if not facts:
            logger.warning("No facts provided for quiz building")
            return []

        # Prepare and filter facts
        prepared_facts = self._prepare_facts(facts)

        if len(prepared_facts) < count:
            count = len(prepared_facts)
            logger.info(f"Not enough facts, reducing count to {count}")

        if count == 0:
            return []

        # Select candidate facts
        selected_facts = self._select_candidate_facts(prepared_facts, count)

        # Generate questions
        questions = self._generate_questions(selected_facts, prepared_facts)

        return questions

    # =========================================================================
    # PRIVATE HELPERS
    # =========================================================================

    def _get_concept_type(self, fact: Dict[str, Any]) -> str:
        """Get concept type from fact with fallback."""
        if "concept_type" in fact and fact["concept_type"]:
            return fact["concept_type"]
        if "type" in fact and fact["type"]:
            return fact["type"]
        return "concept"

    def _get_supporting_fact(self, fact: Dict[str, Any]) -> str:
        """Get supporting fact from fact dictionary."""
        return (
            fact.get("supporting_fact") or
            fact.get("sentence") or
            fact.get("definition") or
            ""
        )

    def _select_question_type(self, concept_type: str,
                              distractors: List[str]) -> str:
        """
        Select an appropriate question type for the concept.

        Args:
            concept_type: The concept type
            distractors: Available distractors

        Returns:
            Selected question type
        """
        # Get recommended types for this concept type
        recommended_types = get_question_types_for_type(concept_type)

        # Get weights for this type
        weights = self.type_weights.get(
            concept_type,
            self.type_weights.get("concept", {})
        )

        # Filter to recommended types
        available_types = [t for t in weights.keys() if t in recommended_types]

        if not available_types:
            available_types = ["definition"]

        # Avoid comparison if not enough distractors
        if len(distractors) < 2 and "comparison" in available_types:
            available_types.remove("comparison")

        if not available_types:
            available_types = ["definition"]

        # Normalize weights
        total_weight = sum(weights.get(t, 1.0) for t in available_types)
        question_weights = [
            weights.get(t, 1.0) / total_weight for t in available_types
        ]

        # Select question type
        return random.choices(available_types, weights=question_weights)[0]

    def _build_question_text(self, question_type: str, concept: str,
                              definition: str, topic: str,
                              distractors: List[str]) -> str:
        """
        Build the question text based on type.

        Delegates to QuestionTemplates for template management.
        """
        return self.templates.build_question_text(
            question_type=question_type,
            concept=concept,
            definition=definition,
            topic=topic,
            distractors=distractors
        )

    def _build_options(self, concept: str,
                       distractors: List[str]) -> Tuple[List[str], str]:
        """
        Build and shuffle options.

        Args:
            concept: The correct concept
            distractors: List of distractor concepts

        Returns:
            Tuple of (formatted_options, correct_letter)
        """
        # Limit to 3 distractors
        distractors = distractors[:3]

        # Build options list
        options = [concept] + distractors

        # Shuffle
        random.shuffle(options)

        # Format options
        formatted_options = [
            f"{chr(65 + i)}) {opt}" for i, opt in enumerate(options)
        ]

        # Find correct letter
        correct_letter = chr(65 + options.index(concept))

        return formatted_options, correct_letter

    def _build_explanation(self, question_text: str, options: List[str],
                           correct_letter: str, correct_text: str,
                           supporting_fact: str) -> str:
        """
        Build explanation using supporting fact.

        This is a simplified version of the explanation builder.
        For full explanation building, use GroundingProcessor.
        """
        if not supporting_fact:
            return f"{correct_text} is the correct answer."

        return f"{correct_text} is correct because {supporting_fact}"

    def _prepare_facts(self, facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prepare and filter facts for quiz generation.

        Steps:
        1. Deduplicate by concept
        2. Log concept type distribution
        """
        # Deduplicate by concept
        unique_facts = self._deduplicate_facts(facts)

        # Log type distribution
        self._log_type_distribution(unique_facts)

        return unique_facts

    def _deduplicate_facts(self, facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate facts by concept name."""
        seen = set()
        unique = []

        for f in facts:
            concept_lower = f.get("concept", "").lower()
            if concept_lower and concept_lower not in seen:
                seen.add(concept_lower)
                unique.append(f)

        return unique

    def _log_type_distribution(self, facts: List[Dict[str, Any]]) -> None:
        """Log concept type distribution for debugging."""
        type_counts = {}
        for f in facts:
            ct = self._get_concept_type(f)
            type_counts[ct] = type_counts.get(ct, 0) + 1

        if type_counts:
            logger.info("Concept type distribution:")
            for type_name, count in type_counts.items():
                logger.info(f"  {type_name}: {count} facts")

    def _select_candidate_facts(self, facts: List[Dict[str, Any]],
                                count: int) -> List[Dict[str, Any]]:
        """
        Select the best facts for quiz generation.

        Prioritizes facts with more compatible distractors.
        """
        scored_facts = []

        for f in facts:
            compatible = self.distractor_selector.get_compatible_facts(facts, f)
            score = len(compatible)  # More compatible = better chance for good distractors
            scored_facts.append((f, score))

        # Sort by score (highest first)
        scored_facts.sort(key=lambda x: x[1], reverse=True)

        # Select top facts
        selected = [f for f, _ in scored_facts[:count]]

        return selected

    def _generate_questions(self, selected_facts: List[Dict[str, Any]],
                            all_facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate questions for selected facts.

        Args:
            selected_facts: Facts selected for question generation
            all_facts: All available facts (for distractor selection)

        Returns:
            List of generated questions
        """
        questions = []

        for fact in selected_facts:
            concept = fact.get("concept", "")
            concept_type = self._get_concept_type(fact)

            # Select distractors
            distractors = self.distractor_selector.select_distractors(
                all_facts, fact, count=3
            )

            if len(distractors) < 2:
                logger.warning(
                    f"Not enough compatible distractors for '{concept}' "
                    f"(type: {concept_type}), skipping"
                )
                continue

            # Build question
            question = self.build_question(fact, distractors)

            if question:
                questions.append(question)
                logger.info(
                    f"Generated '{concept_type}' question for '{concept}' "
                    f"with {len(distractors)} distractors"
                )

        return questions


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def build_question(fact: Dict[str, Any],
                   distractors: List[str]) -> Optional[Dict[str, Any]]:
    """
    Convenience function for building a single question.

    Args:
        fact: Validated fact dictionary
        distractors: List of distractor concept names

    Returns:
        Complete question dictionary, or None if building fails
    """
    builder = QuestionBuilder()
    return builder.build_question(fact, distractors)


def build_quiz(facts: List[Dict[str, Any]],
               count: int = 3) -> List[Dict[str, Any]]:
    """
    Convenience function for building a quiz.

    Args:
        facts: List of validated fact dictionaries
        count: Number of questions to generate

    Returns:
        List of complete question dictionaries
    """
    builder = QuestionBuilder()
    return builder.build_quiz(facts, count)


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    # This test block is kept for backward compatibility but uses the new API
    from app.rag.fact_cache import FactCache

    cache = FactCache()
    cache.load()

    builder = QuestionBuilder()
    facts = cache.get_facts("Algorithms")

    if facts:
        questions = builder.build_quiz(facts, count=3)

        print("\n📝 Generated Quiz:")
        for i, q in enumerate(questions):
            print(f"\nQ{i+1}: {q['question']}")
            print(f"Options: {q['options']}")
            print(f"Correct: {q['correct_letter']} ({q['correct_answer']})")
            print(f"Difficulty: {q.get('difficulty', 0.5):.2f}")
            print(f"Question Type: {q.get('question_type', 'unknown')}")
            print(f"Concept Type: {q.get('concept_type', 'unknown')}")
            print(f"Explanation: {q.get('explanation', '')[:100]}...")
    else:
        print("No facts found for Algorithms")