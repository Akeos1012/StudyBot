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
from app.monitoring.metrics_context import MetricsContext

from .fill_blank_generator import FillBlankGenerator
from .question_explanation import build_consistent_explanation
from ..storage.question_cache import QuestionCache
from .question_scorer import QuestionScorer
from ..utils.question_similarity import is_similar_to_pool
from .question_prompt import build_fact_question_prompt
from ..metadata.question_types import QuestionType
from ..metadata.question_diversity import select_question_type
from app.rag.fact_cache import FactCache
from app.quiz.validation.fact_validator import FactValidator
from .llm_parser import LLMParser
from .llm_client import LLMClient
from .retry_policy import get_failure_type, FailureType
import traceback
from app.config import settings
from app.models.fact_schema import normalize_fact
from .distractor_selector import DistractorSelector
import random

from app.utils.performance_profiler import profile_time
from app.utils.question_id import generate_question_id

from ..validation.question_semantic import (
    validate_semantic,
)

from ..utils.options_parser import get_correct_text_from_options, normalize_options

from ..validation.question_grounding import (
    validate_grounding,
    attach_grounding_fields,
    question_equals_answer,
)

from ..validation.question_validator import (
    validate_distractors,
    validate_structure,
    normalize_and_validate_correct_field,
    validate_question_focus,
    validate_question_uniqueness,
    is_relevant_to_topic,
)

from ..validation.domain_validator import validate_domain_correctness
from app.rag.retriever import Retriever


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
        self.fact_validator = FactValidator()
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
        metrics_context: Optional[MetricsContext] = None,
    ) -> Optional[dict]:
        """
        Generate a question with tiered retries if validation fails.
        """
        validation_error_context = None

        for attempt in range(max_attempts):

            print(f"🔄 Generation attempt {attempt + 1}/{max_attempts}")

            # Inject validation error context if not the first attempt
            current_fact = fact
            if validation_error_context and isinstance(validation_error_context, str):
                # Ensure validation error is bounded and concise
                # Using 150 chars to keep the prompt overhead small
                if len(validation_error_context) > 150:
                    concise_error = validation_error_context[:147] + "..."
                else:
                    concise_error = validation_error_context
                    
                # Attempt 3: Simpler fallback prompt
                if attempt == max_attempts - 1:
                    current_fact = f"SIMPLIFY: Create an easier question for concept '{answer}'. FACT: {fact}\n\nPREVIOUS ERROR: {concise_error}"
                else:
                    current_fact = f"{fact}\n\nPREVIOUS ERROR (CORRECT THIS): {concise_error}"
            elif validation_error_context:
                # Fallback if error is not a string
                current_fact = f"{fact}\n\nPREVIOUS ERROR (NON-STRING): {str(validation_error_context)[:100]}"

            if attempt > 0:
                if metrics_context and metrics_context.quiz_metrics:
                    metrics_context.quiz_metrics.llm_retry_count += 1

            self._supporting_facts = supporting_facts or []

            # Attempt generation
            question, error_context = self.generate_from_fact(
                current_fact,
                answer,
                topic,
                fact_data,
                style_hint=None,
                question_type=question_type,
                metrics_context=metrics_context
            )
            
            print(f"DEBUG: generate_from_fact returned: {question}, error: {error_context}")
            
            # Check if this failure is retryable
            if not question and error_context:
                failure_type = get_failure_type(error_context)
                if failure_type == FailureType.NON_RETRYABLE:
                    print(f"🛑 Deterministic failure (non-retryable): {error_context}. Skipping retries.")
                    return None
            
            validation_error_context = error_context

            if question:
                if attempt == 0:
                    if metrics_context and metrics_context.quiz_metrics:
                        metrics_context.quiz_metrics.accepted_first_try += 1
                else:
                    if metrics_context and metrics_context.quiz_metrics:
                        metrics_context.quiz_metrics.accepted_after_retry += 1
                return question
            print(f"⚠️ Generation attempt {attempt + 1}/{max_attempts} failed: {error_context}")
        
        if metrics_context and metrics_context.quiz_metrics:
            metrics_context.quiz_metrics.failed_after_max_retries += 1
        
        logger.error("PIPELINE FAILURE | Stage: max_retries | Reason: Failed after %s attempts. Last error: %s", max_attempts, validation_error_context)
            
        return None

    def generate_from_fact(
        self,
        fact: str,
        answer: str,
        topic: str,
        fact_data: dict = None,
        style_hint: str = None,
        question_type: str = "multiple",
        metrics_context=None,
    ) -> Tuple[Optional[dict], Optional[str]]:

        """
        Generate a question from a single fact with coherence checking.

        Args:
            fact: The supporting fact text
            answer: The correct answer/concept
            topic: The topic name
            fact_data: Structured fact dictionary
            style_hint: Optional style hint for question phrasing

        Returns:
            Validated question or None, and failure reason if None
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
            logger.warning("VALIDATION FAILED | Stage: sanitization | Reason: Sanitization failed")
            if metrics_context and metrics_context.quiz_metrics:
                metrics_context.quiz_metrics.add_failure("sanitization")
            return None, "Sanitization failed"

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
            logger.warning("VALIDATION FAILED | Stage: grounding | Reason: Answer not grounded in fact")
            if metrics_context and metrics_context.quiz_metrics:
                metrics_context.quiz_metrics.add_failure("grounding")
            return None, f"Answer '{answer}' not grounded in fact"

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

            if metrics_context and metrics_context.quiz_metrics:
                metrics_context.quiz_metrics.record_llm_call(duration)
                        
            print(f"Fact-based response received: {len(content)} characters")

            # Parse response
            result = self.parser.parse(content)

            if result is None:
                logger.warning("VALIDATION FAILED | Stage: json_parse | Reason: Failed to parse LLM response")
                if metrics_context and metrics_context.quiz_metrics:
                    metrics_context.quiz_metrics.add_failure("json_parse")
                return None, "JSON parsing failed"

            questions = self.parser.extract_questions(result)

            if not questions:
                logger.warning("VALIDATION FAILED | Stage: json_parse | Reason: No questions found")
                if metrics_context and metrics_context.quiz_metrics:
                    metrics_context.quiz_metrics.add_failure("json_parse")
                return None, "No questions extracted from JSON"

            question = questions[0]
            
            # Ensure 4 options (rejected if not possible)
            all_topic_facts = self.fact_cache.get_facts(topic)
            distractors = self.distractor_selector.select_distractors(
                all_topic_facts,
                fact_data,
                count=3,
            )

            if len(distractors) < 3:
                return None, "Insufficient distractors found"

            # Ensure distractors and answer make 4
            options = distractors + [answer]

            # Shuffle options while keeping the correct-answer letter synchronized.
            random.shuffle(options)

            # Format options with letter prefixes (e.g., "A) Option")
            question["options"] = normalize_options(options)

            # The validator expects "correct" to identify the actual
            # position of the correct answer after shuffling.
            correct_index = options.index(answer)
            question["correct"] = chr(ord("A") + correct_index)
            question["correct_text"] = answer

            # Propagate fact metadata onto question object
            question["topic"] = question.get("topic") or fact_data.get("topic") or topic
            question["subtopic"] = question.get("subtopic") or fact_data.get("subtopic") or ""
            question["source_note"] = question.get("source_note") or fact_data.get("source_note") or fact_data.get("source") or ""
            question["fact_id"] = question.get("fact_id") or fact_data.get("fact_id") or ""
            question["concept_type"] = question.get("concept_type") or fact_data.get("concept_type") or "concept"
            question["concept"] = question.get("concept") or fact_data.get("concept") or answer
            question["cognitive_type"] = question_style
            question["supporting_fact"] = question.get("supporting_fact") or sanitized_supporting_fact
            question["correct_text"] = question.get("correct_text") or answer

            # Auto-generate explanation if empty
            if not question.get("explanation"):
                question["explanation"] = build_consistent_explanation(
                    question_text=question.get("question", ""),
                    options=question.get("options", []),
                    correct_letter=question.get("correct", ""),
                    correct_text=answer,
                    context=sanitized_supporting_fact,
                    facts=[{"supporting_fact": sanitized_supporting_fact}]
                )

            # ===== VALIDATION PIPELINE =====

            print(f"DEBUG: Question before validation: {question}")
            if not validate_structure(question, metrics_context=metrics_context):
                print("DEBUG: validate_structure failed")
                return None, "Structural validation failed"

            if not validate_distractors(question, metrics_context=metrics_context):
                print("DEBUG: validate_distractors failed")
                return None, "Distractor validation failed"

            if not validate_grounding(question, fact, supporting_fact=sanitized_supporting_fact, metrics_context=metrics_context):
                print("DEBUG: validate_grounding failed")
                return None, "Grounding validation failed"

            if not is_relevant_to_topic(
                question.get('question', ''),
                topic,
                answer,
                sanitized_supporting_fact,
                fact_topic=fact_data.get("topic", ""),
                concept=fact_data.get("concept", ""),
                metrics_context=metrics_context
            ):
                print("DEBUG: is_relevant_to_topic failed")
                return None, "Relevance validation failed"

            if question_equals_answer(question.get('question', ''), question.get('options', [])):
                logger.warning("VALIDATION FAILED | Stage: content | Reason: Question restates the answer")
                if metrics_context and metrics_context.quiz_metrics:
                    metrics_context.quiz_metrics.add_failure("content")
                print("DEBUG: question_equals_answer failed")
                return None, "Question restates the answer"

            if not validate_question_focus(
                question,
                answer,
                supporting_fact=sanitized_supporting_fact,
                metrics_context=metrics_context
            ):
                print("DEBUG: validate_question_focus failed")
                return None, "Focus validation failed"
                
            if not validate_question_uniqueness(question, metrics_context=metrics_context):
                print("DEBUG: validate_question_uniqueness failed")
                return None, "Uniqueness validation failed"

            if not validate_semantic(question):
                logger.warning("VALIDATION FAILED | Stage: semantic | Reason: Semantic validation failed")
                if metrics_context and metrics_context.quiz_metrics:
                    metrics_context.quiz_metrics.add_failure("semantic")
                print("DEBUG: validate_semantic failed")
                return None, "Semantic validation failed"

            if not validate_domain_correctness(
                question,
                answer,
                sanitized_supporting_fact,
            ):
                print("DEBUG: validate_domain_correctness failed")
                return None, "Domain validation failed"

            if not normalize_and_validate_correct_field(question, metrics_context=metrics_context):
                print("DEBUG: normalize_and_validate_correct_field failed")
                return None, "Correct field normalization failed"

            # Quality scoring
            facts = self.retriever.retrieve(topic=topic, limit=settings.RETRIEVAL_LIMIT)
            is_acceptable, score, scores = self._check_quality(question, facts)

            if not is_acceptable:
                logger.warning("VALIDATION FAILED | Stage: quality | Reason: Quality check failed (score: %.2f)", score)
                if metrics_context and metrics_context.quiz_metrics:
                    metrics_context.quiz_metrics.add_failure("quality")
                print(f"DEBUG: _check_quality failed, score: {score:.2f}")
                return None, f"Quality check failed (score: {score:.2f})"

            question['_quality_score'] = score
            question['_quality_scores'] = scores

            return question, None

        except Exception as e:
            return None, f"Unexpected error: {str(e)}"

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
        supporting_facts: list = None,
        metrics_context=None,
        exclude_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate grounded multiple-choice questions from extracted facts.

        Args:
            topic: The topic name
            count: Number of questions to generate
            supporting_facts: List of extracted fact dictionaries
            metrics_context: Metrics context for isolation
            exclude_ids: List of question_ids to exclude from selection

        Returns:
            Dictionary with 'questions' key containing list of validated questions
        """

        self._supporting_facts = supporting_facts or []

        cached_questions = self.cache.sample(
            topic=topic,
            count=count,
            exclude_ids=exclude_ids
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
            logger.error("Generation failed: No supporting facts provided.")
            if metrics_context and metrics_context.quiz_metrics:
                metrics_context.quiz_metrics.add_failure("generation_failed_no_supporting_facts")
            print("⚠️ No supporting facts provided. Cannot generate grounded questions.")
            return {"questions": []}

        valid_questions = []
        
        # Use set of unique facts to avoid redundant retries on the same fact data
        unique_facts = []
        seen_fact_ids = set()
        for fact in supporting_facts:
            fact_data = normalize_fact(fact)
            if not fact_data:
                continue
            fact_id = fact_data.get("fact_id")
            if fact_id and fact_id not in seen_fact_ids:
                unique_facts.append(fact_data)
                seen_fact_ids.add(fact_id)
        
        generation_pool = unique_facts

        # Import diversity scorer
        from app.quiz.metadata.question_diversity import calculate_diversity_score

        # Track batch diversity
        current_batch = []

        for fact_data in generation_pool[:remaining * settings.FACT_MULTIPLIER]:
            print(f"DEBUG: Processing fact: {fact_data}")
            if not isinstance(fact_data, dict):
                continue

            # Ensure fact follows the shared schema
            fact_data = normalize_fact(fact_data)

            # --- PRE-VALIDATION ---
            validation_result = self.fact_validator.validate(fact_data)
            if not validation_result.valid:
                logger.warning(f"Fact pre-validation failed: {validation_result.reason}")
                continue
            # --- /PRE-VALIDATION ---

            if not fact_data:
                logger.warning("VALIDATION FAILED | Stage: fact_normalization | Reason: Normalized fact is empty")
                if metrics_context and metrics_context.quiz_metrics:
                    metrics_context.quiz_metrics.add_failure("fact_normalization")
                continue
            print(f"DEBUG: Normalized fact: {fact_data}")

            concept = fact_data.get("concept", "").strip()
            definition = (
                fact_data.get("supporting_fact")
                or fact_data.get("definition")
                or fact_data.get("sentence")
                or ""
            )

            # Check similarity first (Hard Reject)
            # Assuming is_similar_to_pool exists in QuizGenerator scope based on previous context
            if is_similar_to_pool(
                {"question": definition, "correct_text": concept, "supporting_fact": definition},
                self.cache.sample(topic=topic, count=100) or []
            ):
                logger.warning("VALIDATION FAILED | Stage: similarity | Reason: Fact similar to pool")
                if metrics_context and metrics_context.quiz_metrics:
                    metrics_context.quiz_metrics.add_failure("similarity")
                print(f"DEBUG: Similarity check FAILED")
                continue
            print(f"DEBUG: Similarity check PASSED")

            # Diversity Check (Soft Filter)
            candidate = {
                "concept": concept,
                "difficulty": "medium", # Default for now
                "type": "multiple_choice"
            }
            
            diversity_score = calculate_diversity_score(candidate, current_batch)
            
            # If batch is still small, don't be too strict
            if len(current_batch) > 1 and diversity_score < 0.4:
                logger.warning("VALIDATION FAILED | Stage: diversity | Reason: Low diversity score")
                if metrics_context and metrics_context.quiz_metrics:
                    metrics_context.quiz_metrics.add_failure("diversity")
                print(f"DEBUG: Diversity check FAILED")
                continue
            print(f"DEBUG: Diversity check PASSED")

            llm_start = time.perf_counter()

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
                metrics_context=metrics_context
            )
            print(f"DEBUG: generate_with_retry returned: {question}")

            # Skip fact if fill blank generation failed
            if question is None:
                continue

            if question:
                if question.get("type", "mcq") != "fill_blank":

                    print("\nGENERATED QUESTION BEFORE VALIDATION:")
                    print(question)

                    if not validate_structure(question, metrics_context=metrics_context):
                        print("❌ validate_structure FAILED")
                        print(question)
                        return None
                    
                    if not validate_distractors(question, metrics_context=metrics_context):
                        print("❌ FAILED: distractor validation")
                        continue

                    print(f"DEBUG: Calling validate_semantic")
                    if not validate_semantic(question):
                        print(f"DEBUG: validation_semantic FAILED")
                        if metrics_context:
                            print(f"DEBUG: metrics_context exists")
                            if metrics_context.quiz_metrics:
                                print(f"DEBUG: metrics_context.quiz_metrics exists")
                                metrics_context.quiz_metrics.add_failure("semantic")
                        else:
                            print(f"DEBUG: metrics_context is None")
                        print("❌ FAILED: semantic validation")
                        continue

                    if not validate_domain_correctness(
                        question,
                        concept,
                        definition
                    ):
                        if metrics_context and metrics_context.quiz_metrics:
                            metrics_context.quiz_metrics.add_failure("domain")
                        print("❌ FAILED: domain correctness")
                        continue

                    print("✅ PASSED ALL VALIDATORS")

                if question:

                    if question.get("type") not in ["multiple_choice", "fill_blank"]:
                        if metrics_context and metrics_context.quiz_metrics:
                            metrics_context.quiz_metrics.add_failure("unsupported_type")
                        print("❌ Skipping unsupported question type")
                        continue

                    # Combine current batch and persistent pool for duplicate detection
                    full_pool = valid_questions + (self.cache.get_pool(topic=topic) or [])
                    if is_similar_to_pool(
                        question,
                        full_pool,
                        threshold=SIMILARITY_THRESHOLD
                    ):
                        if metrics_context and metrics_context.quiz_metrics:
                            metrics_context.quiz_metrics.add_failure("similarity")
                        print("❌ Skipped duplicate during generation")
                        continue

                    # Prevent same concept appearing multiple times
                    existing_concepts = {
                        q.get("concept", "").lower()
                        for q in valid_questions
                    }

                    if concept.lower() in existing_concepts:
                        if metrics_context and metrics_context.quiz_metrics:
                            metrics_context.quiz_metrics.add_failure("duplicate_concept")
                        print(
                            f"❌ Duplicate concept skipped: {concept}"
                        )
                        continue

                    valid_questions.append(question)
                    current_batch.append(question)
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

            for q in valid_questions:
                q["question_id"] = generate_question_id(q.get("question", ""))

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