# ============================================================================
# MODULE: QuizGenerator
# LOCATION: app/quiz/quiz_generator.py
#
# PIPELINE POSITION:
#
# FactCache
#    |
#    v
# QuizGenerator
#    |
#    +--> LLMClient (question wording only)
#    |
#    +--> Validation Pipeline
#    |
#    +--> QuestionCache
#
# MAIN PURPOSE:
# Converts trusted extracted FACTS into quiz questions.
#
# CORE RULE:
# The LLM does NOT create knowledge.
# The LLM only transforms existing facts into question format.
#
# INPUT:
# - Extracted facts from RAG pipeline
# - Topic
# - Question count
#
# OUTPUT:
# - Validated quiz questions
#
# IMPORTANT DEPENDENCIES:
# - fact_cache.py       -> source of truth
# - retriever.py        -> retrieves supporting facts
# - llm_client.py       -> generates wording
# - question_validator -> rejects invalid questions
# - question_grounding -> verifies fact alignment
# - question_scorer    -> quality evaluation
# - question_cache     -> stores accepted questions
#
# AUDIT STATUS:
# CORE MODULE - modify carefully
# ============================================================================

import json
import re
import time
import logging

logger = logging.getLogger(__name__)

from difflib import SequenceMatcher
from json_repair import repair_json
from typing import List, Dict, Any, Optional, Tuple

from .fill_blank_generator import FillBlankGenerator
from .question_explanation import build_consistent_explanation
from .question_cache import QuestionCache
from .question_scorer import QuestionScorer
from .question_similarity import is_similar_to_pool
from .question_prompt import build_fact_question_prompt
from .question_types import QuestionType
from .question_diversity import select_question_type
from ..rag.fact_cache import FactCache
from .llm_parser import LLMParser
from .llm_client import LLMClient
import traceback
from app.config import settings
from app.models.fact_schema import normalize_fact
from .distractor_selector import DistractorSelector
import random

from app.utils.performance_profiler import profile_time

from .question_semantic import (
    validate_semantic,
)

from .validation_logger import log_validation_failure

from .options_parser import get_correct_text_from_options

from .question_grounding import (
    validate_grounding,
    attach_grounding_fields,
    question_equals_answer,
)

from .question_validator import (
    validate_distractors,
    validate_structure,
    normalize_and_validate_correct_field,
    validate_question_focus,
    validate_question_uniqueness,
    is_relevant_to_topic,
)

from .validation_logger import (
    log_validation_failure,
    get_metrics,
)

from .domain_validator import validate_domain_correctness
from ..rag.retriever import Retriever


# ============================================================================
# CONSTANTS / VALIDATION RULES
#
# These rules prevent:
#
# - generic concepts
# - hallucinated concepts
# - structural answers
# - duplicate questions
#
# Used mainly by:
# - QuizGenerator.generate_from_fact()
# - QuizGenerator.generate_questions()
# ============================================================================

# Banned layer phrases that indicate structural rather than factual content
BANNED_LAYER_PATTERNS = [
    r'foundational layer',
    r'communication layer',
    r'performance layer',
    r'control layer',
    r'execution layer',
    r'learning layer',
    r'optimization layer',
    r'architecture layer',
    r'layer that',
    r'layer allows',
    r'layer provides',
    r'layer enables',
    r'layer manages',
]

# Words that indicate invalid concepts (verbs, adjectives, generic terms)
INVALID_CONCEPT_WORDS = {
    'allows', 'provides', 'enables', 'stores', 'manages', 'reduces', 'improves',
    'uses', 'supports', 'offers', 'helps', 'contains', 'includes', 'does', 'doing',
    'responsible', 'processing', 'maintaining', 'organizing', 'allow', 'provide',
    'enable', 'store', 'manage', 'reduce', 'improve', 'use', 'support', 'offer',
    'help', 'contain', 'include', 'do', 'concept', 'example', 'method', 'approach',
    'technique', 'process', 'system', 'layer', 'type', 'category', 'classification',
    'service', 'platform', 'solution', 'resource', 'infrastructure', 'component',
    'module'
}

MAX_FACTS_PER_REQUEST = settings.MAX_FACTS_PER_REQUEST
SIMILARITY_THRESHOLD = settings.SIMILARITY_THRESHOLD

MIN_QUALITY_SCORE = settings.MIN_QUALITY_SCORE
DEFAULT_MAX_ATTEMPTS = settings.MAX_GENERATION_RETRIES
DEFAULT_MODEL = settings.LLM_MODEL

# PIPELINE CHECKPOINT:
# Validation Stage:
# Question uniqueness filtering
#
# CONNECTED MODULES:
# - question_similarity.py
# - question_cache.py
#
# USED BY:
# - QuizGenerator.generate_questions()
#
# RESPONSIBILITY:
# Removes duplicate questions before caching or returning results.
#
# DOES NOT:
# - generate questions
# - validate correctness
# - modify facts


def filter_similar_questions(
    questions: List[Dict[str, Any]],
    threshold: float = 0.6
) -> List[Dict[str, Any]]:
    """
    Remove duplicate questions and similar answers.

    Args:
        questions: List of question dictionaries
        threshold: Similarity threshold (0.0 to 1.0)

    Returns:
        Filtered list of unique questions
    """
    if not questions:
        return []

    unique = []
    seen_answers = []

    for q in questions:
        correct_letter = q.get('correct', '')
        options = q.get('options', [])

        correct_text = get_correct_text_from_options(
            options,
            correct_letter
        ).lower()

        # Check answer similarity
        duplicate_answer = False

        if correct_text:
            for seen in seen_answers:
                similarity = SequenceMatcher(
                    None,
                    correct_text,
                    seen
                ).ratio()

                if similarity > 0.95 and correct_text == seen:
                    duplicate_answer = True
                    break

        if duplicate_answer:
            print(f"❌ Removed duplicate answer: {q['question']}")
            continue

        # Check question similarity
        if is_similar_to_pool(q, unique, threshold=0.95):
            print(f"❌ Removed similar question: {q['question']}")
            continue

        unique.append(q)

        if correct_text:
            seen_answers.append(correct_text)

    return unique


def is_layer_phrase(text: str) -> bool:
    """Check if a supporting fact contains generic layer phrases."""
    text_lower = text.lower()
    for pattern in BANNED_LAYER_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False


def sanitize_supporting_fact(supporting_fact: str, concept: str) -> Optional[str]:
    """Sanitize a supporting fact to remove generic layer phrases."""
    if not supporting_fact:
        return None

    if "layer" in concept.lower():
        return supporting_fact

    if is_layer_phrase(supporting_fact):
        print(f"⚠️ Rejecting supporting fact with banned layer phrase: {supporting_fact[:60]}...")
        return None

    return supporting_fact


# ============================================================================
# CORE PIPELINE CONTROLLER
#
# This class connects:
#
# RAG FACTS
#    |
#    v
# PROMPT BUILDER
#    |
#    v
# LLM GENERATION
#    |
#    v
# PARSER
#    |
#    v
# VALIDATION PIPELINE
#    |
#    v
# QUESTION CACHE
#
# This is the main orchestration layer of quiz generation.
#
# It should NOT:
# - extract facts
# - clean markdown
# - define fact schemas
#
# It SHOULD:
# - coordinate generation
# - enforce validation order
# - reject invalid outputs
# ============================================================================

class QuizGenerator:
    """
    Orchestrates grounded question generation from extracted facts.

    The LLM is ONLY used to transform facts into questions. It never invents
    knowledge, answers, or concepts. All questions are validated against
    their source facts before being returned.
    """

# INITIALIZATION CHECKPOINT:
#
# Creates all services required for question generation.
#
# Creates:
# - LLM connection
# - Fact storage access
# - Retriever
# - Parser
# - Scorer
# - Distractor generator
#
# If this breaks:
# Quiz generation pipeline cannot start.

    def __init__(
        self,
        model=DEFAULT_MODEL,
        min_quality_score=MIN_QUALITY_SCORE,
        cache=None,
        fact_cache=None,
        llm_client=None,
    ):
        self.model = model
        self.llm = LLMClient(model=model)
        self.fill_blank_generator = FillBlankGenerator()

        # Cache of previously generated questions
        self.cache = cache or QuestionCache()
        self.fact_cache = fact_cache or FactCache()
        self.llm = llm_client or LLMClient(model=model)

        # Knowledge base
        self.fact_cache = fact_cache or FactCache()

        if fact_cache is None:
            self.fact_cache.load()

        # Fact retriever
        self.retriever = Retriever(self.fact_cache)

        self.parser = LLMParser()
        self.scorer = QuestionScorer()
        self.min_quality_score = min_quality_score
        self.distractor_selector = DistractorSelector()

        # State for current generation
        self._supporting_facts = []

        # Metrics tracking
        self._llm_calls = 0
        self._llm_time = 0.0
        self._generated_questions = []

    # =========================================================================
    # METRICS
    # =========================================================================

    def _record_llm_usage(self, response_content: str, duration: float = 0.0):
        """Track LLM usage for reporting."""
        self._llm_calls += 1
        self._llm_time += duration

    def get_metrics(self) -> Dict[str, Any]:
        """Return current LLM usage metrics."""
        return {
            'llm_calls': self._llm_calls,
            'llm_time': self._llm_time,
            'facts_used': len(self._supporting_facts),
            'questions_generated': len(self._generated_questions)
        }

    # =========================================================================
    # QUALITY CHECK
    # =========================================================================

    def _check_quality(self, question: dict, facts: list = None) -> Tuple[bool, float, Dict[str, float]]:
        """Check question quality using QuestionScorer."""
        if facts is None:
            facts = []

        is_acceptable, score, scores, issues = self.scorer.is_acceptable(question, facts)

        if not is_acceptable:
            print(f"⚠️ Quality check failed: score={score:.2f} (threshold={self.min_quality_score})")
            print(f"   Scores: {scores}")
            print(f"   Issues: {issues}")
        else:
            print(f"✅ Quality check passed: score={score:.2f}")

        return is_acceptable, score, scores

# GENERATION CHECKPOINT:
#
# PURPOSE:
# Retry failed question generation.
#
# FLOW:
#
# FACT
#  |
#  v
# generate_from_fact()
#  |
#  v
# validation
#
# Failure:
# retry
#
# Success:
# return question
#
# CONNECTED:
# - generate_from_fact()
# - validation_logger
# - quiz_metrics
    
    def generate_with_retry(
        self,
        fact: str,
        answer: str,
        topic: str,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        fact_data: dict = None,
        supporting_facts: list = None,
        question_type: str = "multiple",
    ) -> Optional[dict]:
        """
        Generate a question with retries if validation fails.

        Args:
            fact: The supporting fact text
            answer: The correct answer/concept
            topic: The topic name
            max_attempts: Maximum retry attempts
            fact_data: Structured fact dictionary

        Returns:
            Validated question or None
        """
        for attempt in range(max_attempts):

            print(f"🔄 Generation attempt {attempt + 1}/{max_attempts}")

            if attempt > 0:
                metrics = get_metrics()
                if metrics:
                    metrics.llm_retry_count += 1

            self._supporting_facts = supporting_facts or []


# MAIN GENERATION PIPELINE CHECKPOINT
#
# Converts one trusted FACT into one validated question.
#
# FULL FLOW:
#
# Fact
#  |
#  v
# Sanitize fact
#  |
#  v
# Build prompt
#  |
#  v
# LLM generates wording
#  |
#  v
# Parse JSON
#  |
#  v
# Add distractors
#  |
#  v
# Validation Pipeline:
#
# 1. Structure
# 2. Distractors
# 3. Grounding
# 4. Topic relevance
# 5. Focus
# 6. Semantic
# 7. Domain correctness
# 8. Quality score
#
# Output:
# Accepted question OR None
#
# IMPORTANT:
# This function is the main hallucination barrier.

            print("ANSWER:", answer)
            print("TOPIC:", topic)

            question = self.generate_from_fact(
                fact,
                answer,
                topic,
                fact_data,
                style_hint=None,
                question_type=question_type
            )

            print("RESULT:", question)
            print("==============================\n")
            if question:

                if attempt == 0:
                    metrics = get_metrics()
                    if metrics:
                        metrics.accepted_first_try += 1
                else:
                    metrics = get_metrics()
                    if metrics:
                        metrics.accepted_after_retry += 1

                return question
            print(f"⚠️ Generation attempt {attempt + 1}/{max_attempts} failed")
        return None

    def generate_from_fact(
        self,
        fact: str,
        answer: str,
        topic: str,
        fact_data: dict = None,
        style_hint: str = None,
        question_type: str = "multiple",
    ) -> Optional[dict]:

        """
        Generate a question from a single fact with coherence checking.

        Args:
            fact: The supporting fact text
            answer: The correct answer/concept
            topic: The topic name
            fact_data: Structured fact dictionary
            style_hint: Optional style hint for question phrasing

        Returns:
            Validated question or None
        """
        fact_data = fact_data or {}

        # Build supporting fact from structured data
        supporting_fact = (
            fact_data.get('supporting_fact') or
            fact_data.get('sentence') or
            fact_data.get('definition') or
            fact or
            ""
        )

        # Sanitize supporting fact
        sanitized_supporting_fact = sanitize_supporting_fact(supporting_fact, answer)

        if not sanitized_supporting_fact:
            print(f"⚠️ Skipping fact due to layer phrase: {supporting_fact[:60]}...")
            return None

        fact_for_prompt = sanitized_supporting_fact


        # Prevent LLM hallucinating concepts not supported by fact
        fact_lower = fact_for_prompt.lower()

        # Include the concept name when checking grounding.
        # Some extracted facts store the definition separately from the concept.
        grounding_text = (
            fact_lower +
            " " +
            answer.lower()
        )

        answer_words = [
            w.lower()
            for w in answer.split()
            if len(w) > 3
        ]

        matched = [
            w for w in answer_words
            if w in grounding_text
        ]

        if answer_words and len(matched) < max(1, len(answer_words) // 2):
            print(
                f"⚠️ Skipping fact: answer '{answer}' not grounded in fact"
            )
            return None

        # Build prompt
        question_style = select_question_type()

        prompt = build_fact_question_prompt(
            fact_for_prompt,
            answer,
            topic,
            style_hint=f"""
        The correct answer must appear explicitly or be directly described in the FACT.
        Never use related concepts that are not mentioned.
        """,
            question_type=question_type
        )

        try:
            # Call LLM
            start_time = time.time()
            start_time = time.perf_counter()

            with profile_time("llm_generation"):
                content = self.llm.generate(prompt)

            duration = time.perf_counter() - start_time

            self._record_llm_usage(
                content,
                duration
            )

            metrics = get_metrics()

            if metrics:
                metrics.record_llm_call(duration)
                        
            print(f"Fact-based response received: {len(content)} characters")

            # Parse response
            result = self.parser.parse(content)

            if result is None:
                print("❌ FAILED: parser.parse returned None")
                log_validation_failure(None, "json_parse", "Failed to parse LLM response")
                return None

            questions = self.parser.extract_questions(result)

            if not questions:
                print("❌ FAILED: extract_questions returned empty")
                log_validation_failure(None, "json_parse", "No questions found")
                return None

            question = questions[0]
            print("\n=== PARSED QUESTION ===")
            print(question)

            print(question)
            question["correct"] = answer
            print(question)

            distractors = self.distractor_selector.select_distractors(
                self._supporting_facts,
                fact_data,
                count=3,
            )

            options = distractors + [answer]
            random.shuffle(options)

            letters = ["A", "B", "C", "D"]

            question["options"] = [
                f"{letter}) {option}"
                for letter, option in zip(letters, options)
            ]

            question["correct"] = letters[options.index(answer)]

            question["type"] = "multiple_choice"

            # Propagate fact metadata onto question object
            question["topic"] = question.get("topic") or fact_data.get("topic") or topic
            question["subtopic"] = question.get("subtopic") or fact_data.get("subtopic") or ""
            question["source_note"] = question.get("source_note") or fact_data.get("source_note") or fact_data.get("source") or ""
            question["fact_id"] = question.get("fact_id") or fact_data.get("fact_id") or ""
            question["concept_type"] = question.get("concept_type") or fact_data.get("concept_type") or "concept"
            question["concept"] = question.get("concept") or fact_data.get("concept") or answer
            question["cognitive_type"] = question_style

            # ===== VALIDATION PIPELINE =====

            # Stage 1: Structure
            print(question.get("question"))


            if not validate_structure(question):
                print("❌ validate_structure FAILED")
                print("FAILED QUESTION:")
                print(question.get("question"))
                return None

            # Stage 1.5: Distractors
            if not validate_distractors(question):
                print("❌ validate_distractors FAILED")
                print(question)
                return None

            # Stage 2: Content - Grounding
            print("ANSWER:", answer)

            if not validate_grounding(question, fact, supporting_fact=sanitized_supporting_fact):
                print("❌ validate_grounding FAILED")
                print(question)
                print("FACT:", fact)
                return None

            # Stage 2: Content - Topic relevance
            if not is_relevant_to_topic(
                question.get('question', ''),
                topic,
                answer,
                sanitized_supporting_fact,
                fact_topic=fact_data.get("topic", ""),
                concept=fact_data.get("concept", "")
            ):
                return None

            # Stage 2: Content - Question restates answer
            if question_equals_answer(question.get('question', ''), question.get('options', [])):
                log_validation_failure(question, "content", "Question restates the answer")
                return None

            # Stage 2: Content - Placeholder detection
            q_text = question.get('question', '')
            if 'testing the fact' in q_text.lower() or 'question about' in q_text.lower() and len(q_text) < 40:
                log_validation_failure(question, "content", "Placeholder question detected")
                return None

            # Stage 2: Content - Question focus validation
            if not validate_question_focus(
                question,
                answer,
                supporting_fact=sanitized_supporting_fact
            ):
                log_validation_failure(question, "focus", f"Question doesn't focus on concept '{answer}'")
                return None
            # Stage 2.5: Question uniqueness
            if not validate_question_uniqueness(question):
                return None

            # Stage 3: Semantic
            if not validate_semantic(question):
                log_validation_failure(question, "semantic", "Semantic validation failed")
                return None

            # Stage 4: Domain correctness
            if not validate_domain_correctness(
                question,
                answer,
                sanitized_supporting_fact,
            ):
                return None

            # Stage 5: Correct field normalization
            if not normalize_and_validate_correct_field(question):
                return None

            # Stage 6: Attach grounding fields
            correct_letter = question.get('correct', '')
            correct_text = get_correct_text_from_options(question.get('options', []), correct_letter)
            supporting_fact = question.get('supporting_fact') or fact_data.get('supporting_fact') or fact

            if not attach_grounding_fields(question, correct_text, sanitized_supporting_fact, context=fact):
                print("⚠️ Could not attach grounded explanation for fact-based question")
                # Continue - we already have a fallback in _attach_grounding_fields

            # Stage 7: Quality scoring
            facts = self.retriever.retrieve(topic=topic, limit=settings.RETRIEVAL_LIMIT)
            is_acceptable, score, scores = self._check_quality(question, facts)

            if not is_acceptable:
                print(f"⚠️ Question scored {score:.2f} - below threshold ({self.min_quality_score}), rejecting")
                return None

            question['_quality_score'] = score
            question['_quality_scores'] = scores

            return question

        except Exception:
            traceback.print_exc()
            raise

# HIGH LEVEL GENERATION ENTRY POINT
#
# Called by:
# quiz_service.py
#
# RESPONSIBILITY:
# Generate requested number of questions for a topic.
#
# FLOW:
#
# Topic
#  |
#  v
# Fact list
#  |
#  v
# generate_with_retry()
#  |
#  v
# validate
#  |
#  v
# cache
#  |
#  v
# API response
#
# This function manages batches.
# generate_from_fact() manages individual questions.

    def generate_questions(
        self,
        topic: str,
        count: int = 1,
        supporting_facts: list = None
    ) -> Dict[str, Any]:
        """
        Generate grounded multiple-choice questions from extracted facts.

        Args:
            topic: The topic name
            count: Number of questions to generate
            supporting_facts: List of extracted fact dictionaries

        Returns:
            Dictionary with 'questions' key containing list of validated questions
        """

        self._supporting_facts = supporting_facts or []

        cached_questions = self.cache.sample(
            topic=topic,
            count=count
        )

        pool_size = self.cache.get_pool_size(
            topic=topic,
            subtopic="",
            difficulty="medium",
            qtype="multiple_choice",
        )

        if cached_questions:
            print(
                f"📦 Cache retrieved ({len(cached_questions)} questions, pool={pool_size})"
            )

            if len(cached_questions) >= count:
                # Issue #2 fix: cache has sufficient questions — return them
                # directly.  Previously this branch discarded the cache and
                # forced a full LLM generation on every call ("bypassed for
                # testing").
                return {"questions": cached_questions[:count]}

            remaining = count - len(cached_questions)

        else:
            remaining = count

        # Cache is insufficient — generate the remaining questions via LLM.

        # ===== HALLUCINATION PREVENTION =====
        # Facts are the ONLY source of truth. No raw context is ever sent to the LLM.
        if not supporting_facts:
            print("⚠️ No supporting facts provided. Cannot generate grounded questions.")
            return {"questions": []}

        valid_questions = []
        
        # Process up to 3x requested count for filtering
        generation_pool = supporting_facts * settings.FACT_MULTIPLIER

        for fact_data in generation_pool[:remaining * settings.FACT_MULTIPLIER]:
            if not isinstance(fact_data, dict):
                continue

            # Ensure fact follows the shared schema
            fact_data = normalize_fact(fact_data)

            if not fact_data:
                continue

            concept = fact_data.get("concept", "").strip()
            definition = (
                fact_data.get("supporting_fact")
                or fact_data.get("definition")
                or fact_data.get("sentence")
                or ""
            )

            if not concept or not definition:
                continue

            question_type = select_question_type()

            question = self.generate_with_retry(
                fact=definition,
                answer=concept,
                topic=topic,
                fact_data=fact_data,
                supporting_facts=supporting_facts,
                question_type=question_type,
            )

            # Skip fact if fill blank generation failed
            if question is None:
                continue

            if question:

                if question.get("type", "mcq") != "fill_blank":

                    print("\nGENERATED QUESTION BEFORE VALIDATION:")
                    print(question)

                    if not validate_structure(question):
                        print("❌ validate_structure FAILED")
                        print(question)
                        return None
                    
                    if not validate_distractors(question):
                        print("❌ FAILED: distractor validation")
                        continue

                    if not validate_semantic(question):
                        print("❌ FAILED: semantic validation")
                        continue

                    if not validate_domain_correctness(
                        question,
                        concept,
                        definition
                    ):
                        print("❌ FAILED: domain correctness")
                        continue

                    print("✅ PASSED ALL VALIDATORS")

                if question:

                    if question.get("type") not in ["multiple_choice", "fill_blank"]:
                        print("❌ Skipping unsupported question type")
                        continue

                    if is_similar_to_pool(
                        question,
                        valid_questions,
                        threshold=SIMILARITY_THRESHOLD
                    ):
                        print("❌ Skipped duplicate during generation")
                        continue

                    # Prevent same concept appearing multiple times
                    existing_concepts = {
                        q.get("concept", "").lower()
                        for q in valid_questions
                    }

                    if concept.lower() in existing_concepts:
                        print(
                            f"❌ Duplicate concept skipped: {concept}"
                        )
                        continue

                    valid_questions.append(question)
                    print("✅ ACCEPTED")

                    if len(valid_questions) >= count:
                        break

                else:

                    print("❌ REJECTED")

        if len(valid_questions) < count:
            print(f"⚠️ Only generated {len(valid_questions)} grounded questions out of {count} requested")

        # Filter similar questions
        if len(valid_questions) > 1:
            valid_questions = filter_similar_questions(valid_questions, threshold=SIMILARITY_THRESHOLD)

        # Count only accepted questions
        self._generated_questions.extend(valid_questions)

        if valid_questions:
            print(f"💾 Saving {len(valid_questions)} questions to cache")

            result = self.cache.add_to_pool(
                topic=topic,
                subtopic="",
                difficulty="medium",
                qtype="multiple_choice",
                new_questions=valid_questions,
            )

            print(f"💾 Added result: {result}")

        combined_questions = []

        if cached_questions:
            combined_questions.extend(cached_questions)

        combined_questions.extend(valid_questions)

        return {
            "questions": combined_questions[:count]
        }

    # =========================================================================
    # FILL-IN-THE-BLANK GENERATION
    # =========================================================================

    def generate_fill_blank(
        self,
        topic: str,
        supporting_facts: list = None
    ) -> Dict[str, Any]:
        """
        Generate grounded fill-in-the-blank questions.

        Delegates generation to FillBlankGenerator.
        """

        return self.fill_blank_generator.generate_fill_blank(
            topic,
            supporting_facts
        )


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    context = """
    Cloud computing provides computing resources over the internet.
    Cloud storage allows users to store files remotely.
    Virtual machines create virtualized computing environments.
    Object storage stores data as objects instead of traditional files.
    Cloud databases provide managed database services through cloud platforms.
    """

    gen = QuizGenerator()

    facts = gen.fact_cache.get_facts("Cloud")

    result = gen.generate_questions(
        topic="Cloud",
        count=5,
        supporting_facts=facts
    )

    print(json.dumps(result, indent=2))