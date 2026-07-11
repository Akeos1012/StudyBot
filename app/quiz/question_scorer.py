"""
Question Scorer Module - Pure evaluation of generated questions.

This module is responsible ONLY for evaluating the quality of already-generated
questions. It does NOT modify, generate, or select questions.

Responsibilities:
- Compute weighted quality scores
- Return detailed sub-scores
- Explain why points were deducted

This module does NOT:
- Modify or generate questions
- Choose distractors
- Infer ontology
- Access LLMs
- Duplicate logic from fact_schema.py or options_parser.py
"""

import logging
from typing import Dict, List, Any, Tuple, Optional

from .options_parser import (
    extract_option_text,
    get_correct_text_from_options,
    get_distractor_texts,
    validate_options_format
)
from ..models.question_schema import validate_question_schema

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS
# ============================================================================

# Default weights for scoring dimensions
DEFAULT_WEIGHTS = {
    "schema": 0.25,
    "semantic": 0.30,
    "distractors": 0.25,
    "formatting": 0.10,
    "readability": 0.10
}

# Minimum acceptable overall score
DEFAULT_MIN_SCORE = 0.6

# Stop words for semantic analysis
STOP_WORDS = {
    'the', 'this', 'that', 'with', 'from', 'have', 'will', 'they',
    'what', 'when', 'where', 'which', 'their', 'there', 'about',
    'concept', 'using', 'used', 'also', 'can', 'for', 'are', 'has',
    'its', 'them', 'than', 'then', 'these', 'those'
}

# Ideal overlap range for distractors
IDEAL_OVERLAP_MIN = 0.1
IDEAL_OVERLAP_MAX = 0.4
OVERLAP_TOO_SIMILAR = 0.6

# Maximum question length
MAX_QUESTION_LENGTH = 250

# Maximum explanation length
MAX_EXPLANATION_LENGTH = 200

# ============================================================================
# MAIN CLASS
# ============================================================================

class QuestionScorer:
    """
    Scores questions on multiple quality metrics.

    This class evaluates questions based on:
    1. Schema validity
    2. Semantic consistency
    3. Distractor quality
    4. Formatting quality
    5. Readability

    The scorer is deterministic and side-effect free.

    Usage:
        scorer = QuestionScorer()
        result = scorer.score_question(question, facts)
        if scorer.is_acceptable(question, facts):
            # Use the question
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None,
                 min_acceptable_score: float = DEFAULT_MIN_SCORE):
        """
        Initialize the question scorer.

        Args:
            weights: Dictionary of dimension weights. If None, uses defaults.
            min_acceptable_score: Minimum score for a question to be acceptable.
        """
        self.weights = weights or DEFAULT_WEIGHTS.copy()
        self.min_acceptable_score = min_acceptable_score

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def score_question(self, question: Dict[str, Any],
                       facts: Optional[List[Dict[str, Any]]] = None) -> Tuple[float, Dict[str, float], List[str]]:
        """
        Score a question on quality metrics.

        Args:
            question: The question dictionary to score
            facts: Optional list of facts for context (for type consistency)

        Returns:
            Tuple of (total_score, individual_scores, issues_list)

        Example:
            >>> scorer = QuestionScorer()
            >>> question = {
            ...     "question": "What is SQL?",
            ...     "options": ["A) SQL", "B) NoSQL", "C) MongoDB", "D) PostgreSQL"],
            ...     "correct": "A",
            ...     "explanation": "SQL is a standard language for managing relational databases."
            ... }
            >>> score, scores, issues = scorer.score_question(question)
            >>> print(f"Score: {score:.2f}, Issues: {len(issues)}")
        """
        facts = facts or []

        # Compute individual scores
        schema_score = self._score_schema(question)
        semantic_score = self._score_semantic(question)
        distractor_score = self._score_distractors(question)
        formatting_score = self._score_formatting(question)
        readability_score = self._score_readability(question)

        scores = {
            "schema": schema_score,
            "semantic": semantic_score,
            "distractors": distractor_score,
            "formatting": formatting_score,
            "readability": readability_score
        }

        # Collect issues
        issues = self._collect_issues(question, scores)

        # Calculate weighted total
        total = sum(scores[k] * self.weights.get(k, 0) for k in scores)

        return total, scores, issues

    def is_acceptable(self, question: Dict[str, Any],
                      facts: Optional[List[Dict[str, Any]]] = None) -> Tuple[bool, float, Dict[str, float], List[str]]:
        """
        Check if a question meets the quality threshold.

        Args:
            question: The question dictionary to check
            facts: Optional list of facts for context

        Returns:
            Tuple of (is_acceptable, total_score, individual_scores, issues)
        """
        total, scores, issues = self.score_question(question, facts)
        is_acceptable = total >= self.min_acceptable_score
        return is_acceptable, total, scores, issues

    def get_detailed_report(self, question: Dict[str, Any],
                           facts: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Get a detailed quality report for a question.

        Args:
            question: The question dictionary
            facts: Optional list of facts for context

        Returns:
            Dictionary with comprehensive quality information

        Example:
            >>> report = scorer.get_detailed_report(question)
            >>> print(report["overall_score"])
            0.91
        """
        total, scores, issues = self.score_question(question, facts)

        correct_letter = question.get('correct', '')
        options = question.get('options', [])
        correct_answer = get_correct_text_from_options(options, correct_letter)

        return {
            "overall_score": total,
            "passed": total >= self.min_acceptable_score,
            "scores": scores,
            "issues": issues,
            "correct_answer": correct_answer,
            "correct_letter": correct_letter,
            "num_options": len(options),
            "question_preview": question.get('question', '')[:100] + "..."
        }

    # =========================================================================
    # SCORING DIMENSIONS
    # =========================================================================

    def _score_schema(self, question: Dict[str, Any]) -> float:
        """
        Score schema validity using question_schema.py.

        Checks:
        - Required fields exist
        - Four options
        - Correct answer exists
        - Explanation exists
        """
        if validate_question_schema(question):
            return 1.0
        return 0.0

    def _score_semantic(self, question: Dict[str, Any]) -> float:
        """
        Score semantic consistency.

        Checks:
        - Question matches the correct answer
        - Explanation supports the answer
        - No obvious contradictions
        """
        scores = []

        # Check: Question references the answer
        answer_letter = question.get('correct', '')
        options = question.get('options', [])
        correct_text = get_correct_text_from_options(options, answer_letter)

        if not correct_text:
            return 0.0

        question_text = question.get('question', '').lower()
        correct_lower = correct_text.lower()

        # Level 1: Exact concept reference
        if correct_lower in question_text:
            scores.append(1.0)
        else:
            # Level 2: Word overlap
            correct_words = set(
                w for w in correct_lower.split()
                if len(w) > 3 and w not in STOP_WORDS
            )
            question_words = set(
                w for w in question_text.split()
                if len(w) > 3 and w not in STOP_WORDS
            )

            if correct_words:
                overlap = len(correct_words & question_words) / len(correct_words)
                scores.append(min(overlap * 1.5, 1.0))
            else:
                scores.append(0.5)

        # Check: Explanation supports the answer
        explanation = question.get('explanation', '').lower()
        if explanation:
            # Check if explanation mentions the correct answer
            if correct_lower in explanation:
                scores.append(1.0)
            else:
                # Check for word overlap
                explanation_words = set(
                    w for w in explanation.split()
                    if len(w) > 3 and w not in STOP_WORDS
                )
                if correct_words and explanation_words:
                    overlap = len(correct_words & explanation_words) / len(correct_words)
                    scores.append(min(overlap * 1.5, 1.0))
                else:
                    scores.append(0.5)
        else:
            scores.append(0.0)

        return sum(scores) / len(scores) if scores else 0.0

    def _score_distractors(self, question: Dict[str, Any]) -> float:
        """
        Score distractor quality.

        Checks:
        - Distractors are unique
        - Distractors are not identical to the answer
        - Distractors are reasonably plausible
        - No duplicate options
        """
        answer_letter = question.get('correct', '')
        options = question.get('options', [])

        if not options or len(options) != 4:
            return 0.0

        correct_text = get_correct_text_from_options(options, answer_letter)
        distractors = get_distractor_texts(options, answer_letter)

        if not distractors:
            return 0.0

        # Check: No duplicate options
        option_texts = [extract_option_text(opt) for opt in options]
        if len(set(option_texts)) != len(option_texts):
            return 0.3

        # Check: Distractors are unique
        if len(set(distractors)) != len(distractors):
            return 0.4

        # Score each distractor
        correct_words = set(correct_text.lower().split())
        distractor_scores = []

        for d in distractors:
            d_words = set(d.lower().split())

            # Overlap score: ideal overlap is 0.1-0.4
            if correct_words:
                overlap = len(correct_words & d_words) / max(len(correct_words), 1)

                if IDEAL_OVERLAP_MIN <= overlap <= IDEAL_OVERLAP_MAX:
                    d_score = 1.0
                elif overlap < IDEAL_OVERLAP_MIN:
                    d_score = 0.7  # Too different, might be too easy
                elif overlap >= OVERLAP_TOO_SIMILAR:
                    d_score = 0.3  # Too similar, confusing
                else:
                    d_score = 0.5
            else:
                d_score = 0.5

            # Length similarity
            len_diff = abs(len(correct_text) - len(d))
            if len_diff < 3:
                d_score *= 1.2
            elif len_diff < 6:
                d_score *= 1.0
            else:
                d_score *= 0.8

            distractor_scores.append(min(d_score, 1.0))

        return sum(distractor_scores) / len(distractor_scores)

    def _score_formatting(self, question: Dict[str, Any]) -> float:
        """
        Score formatting quality.

        Checks:
        - Options formatted consistently
        - No empty strings
        - No malformed labels
        """
        options = question.get('options', [])

        if not options or len(options) != 4:
            return 0.0

        # Check format
        if validate_options_format(options):
            format_score = 1.0
        else:
            # Check if options are at least non-empty
            non_empty = all(opt and opt.strip() for opt in options)
            if non_empty:
                format_score = 0.6
            else:
                return 0.0

        # Check for empty option text
        option_texts = [extract_option_text(opt) for opt in options]
        empty_text = any(not text for text in option_texts)

        if empty_text:
            return 0.4

        return format_score

    def _score_readability(self, question: Dict[str, Any]) -> float:
        """
        Score readability quality.

        Checks:
        - Question is understandable
        - Question is not excessively long
        - Explanation is concise
        """
        scores = []

        # Check question length
        q_text = question.get('question', '')
        if q_text and len(q_text) <= MAX_QUESTION_LENGTH:
            scores.append(1.0)
        elif q_text:
            # Penalize long questions
            scores.append(max(0.3, 1.0 - (len(q_text) - MAX_QUESTION_LENGTH) / MAX_QUESTION_LENGTH))
        else:
            scores.append(0.0)

        # Check explanation length
        explanation = question.get('explanation', '')
        if explanation and len(explanation) <= MAX_EXPLANATION_LENGTH:
            scores.append(1.0)
        elif explanation:
            scores.append(max(0.3, 1.0 - (len(explanation) - MAX_EXPLANATION_LENGTH) / MAX_EXPLANATION_LENGTH))
        else:
            # No explanation is a schema issue, not readability
            scores.append(0.5)

        # Check if question ends with ?
        if q_text and q_text.strip().endswith('?'):
            scores.append(1.0)
        else:
            scores.append(0.0)

        return sum(scores) / len(scores) if scores else 0.0

    # =========================================================================
    # ISSUE COLLECTION
    # =========================================================================

    def _collect_issues(self, question: Dict[str, Any],
                       scores: Dict[str, float]) -> List[str]:
        """
        Collect issues that affected the score.

        Args:
            question: The question dictionary
            scores: The computed scores

        Returns:
            List of issue descriptions
        """
        issues = []

        # Schema issues
        if scores.get("schema", 0) < 1.0:
            required = ['question', 'options', 'correct', 'explanation']
            missing = [f for f in required if f not in question]
            if missing:
                issues.append(f"Missing required fields: {', '.join(missing)}")

            options = question.get('options', [])
            if len(options) != 4:
                issues.append(f"Expected 4 options, got {len(options)}")

            if question.get('correct', '') not in ['A', 'B', 'C', 'D']:
                issues.append(f"Invalid correct answer: {question.get('correct')}")

        # Semantic issues
        if scores.get("semantic", 0) < 0.7:
            issues.append("Question may not be semantically consistent with the answer")

            answer_letter = question.get('correct', '')
            options = question.get('options', [])
            correct_text = get_correct_text_from_options(options, answer_letter)

            if correct_text and correct_text.lower() not in question.get('question', '').lower():
                issues.append("Question does not explicitly mention the correct answer")

        # Distractor issues
        if scores.get("distractors", 0) < 0.6:
            issues.append("Distractor quality is low (may be too similar or too different)")

            answer_letter = question.get('correct', '')
            options = question.get('options', [])
            distractors = get_distractor_texts(options, answer_letter)

            if distractors:
                # Check for duplicate distractors
                if len(set(distractors)) != len(distractors):
                    issues.append("Duplicate distractors found")

        # Formatting issues
        if scores.get("formatting", 0) < 0.8:
            issues.append("Option formatting is inconsistent or invalid")

        # Readability issues
        if scores.get("readability", 0) < 0.7:
            q_text = question.get('question', '')
            if len(q_text) > MAX_QUESTION_LENGTH:
                issues.append(f"Question is too long ({len(q_text)} chars)")

            if q_text and not q_text.strip().endswith('?'):
                issues.append("Question does not end with a question mark")

        return issues