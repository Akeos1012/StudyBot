import json
import re
import time
from difflib import SequenceMatcher
from json_repair import repair_json
from typing import List, Dict, Any, Optional, Tuple

from .fill_blank_generator import FillBlankGenerator
from .question_explanation import build_consistent_explanation
from .question_cache import QuestionCache
from .question_scorer import QuestionScorer
from .question_similarity import is_similar_to_pool
from .question_prompt import build_fact_question_prompt
from ..rag.fact_cache import FactCache
from .llm_parser import LLMParser
from .llm_client import LLMClient
import traceback
from app.config import settings
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
# CONSTANTS
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

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

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

                if similarity > 0.90 and is_similar_to_pool(q, unique, 0.85):
                    duplicate_answer = True
                    break

        if duplicate_answer:
            print(f"❌ Removed duplicate answer: {q['question']}")
            continue

        # Check question similarity
        if is_similar_to_pool(q, unique, threshold):
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
# QUIZ GENERATOR CLASS
# ============================================================================

class QuizGenerator:
    """
    Orchestrates grounded question generation from extracted facts.

    The LLM is ONLY used to transform facts into questions. It never invents
    knowledge, answers, or concepts. All questions are validated against
    their source facts before being returned.
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        min_quality_score: float = MIN_QUALITY_SCORE
    ):
        self.model = model
        self.llm = LLMClient(model=model)
        self.fill_blank_generator = FillBlankGenerator(self.llm)

        # Cache of previously generated questions
        self.cache = QuestionCache()

        # Knowledge base
        self.fact_cache = FactCache()
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

    # =========================================================================
    # FACT-BASED GENERATION
    # =========================================================================
    
    
    def generate_with_retry(
        self,
        fact: str,
        answer: str,
        topic: str,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        fact_data: dict = None,
        supporting_facts: list = None,
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

            question = self.generate_from_fact(
                fact,
                answer,
                topic,
                fact_data
            )
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
        style_hint: str = None
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

        # Build prompt
        prompt = build_fact_question_prompt(
            fact_for_prompt,
            answer,
            topic,
            style_hint=style_hint
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
                log_validation_failure(None, "json_parse", "Failed to parse LLM response")
                return None

            questions = self.parser.extract_questions(result)

            if not questions:
                log_validation_failure(None, "json_parse", "No questions found")
                return None

            question = questions[0]

            question["correct"] = answer

            print("\n===== TARGET FACT =====")
            print(fact_data)

            distractors = self.distractor_selector.select_distractors(
                self._supporting_facts,
                fact_data,
                count=3,
            )

            print("===== DISTRACTORS =====")
            print(distractors)

            options = distractors + [answer]

            print("===== FINAL OPTIONS =====")
            print(options)

            random.shuffle(options)

            letters = ["A", "B", "C", "D"]

            question["options"] = [
                f"{letter}) {option}"
                for letter, option in zip(letters, options)
            ]

            question["correct"] = letters[options.index(answer)]

            # ===== VALIDATION PIPELINE =====

            # Stage 1: Structure
            if not validate_structure(question):
                return None

            # Stage 1.5: Distractors
            if not validate_distractors(question):
                return None

            # Stage 2: Content - Grounding
            if not validate_grounding(question, fact, supporting_fact=sanitized_supporting_fact):
                return None

            # Stage 2: Content - Topic relevance
            if not is_relevant_to_topic(
                question.get('question', ''),
                topic,
                answer,
                sanitized_supporting_fact
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
            print("question:", type(question), question)
            print("fact_data:", type(fact_data), fact_data)
            print("fact:", type(fact), fact)
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

    # =========================================================================
    # MULTIPLE CHOICE GENERATION
    # =========================================================================

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

        # ===== HALLUCINATION PREVENTION =====
        # Facts are the ONLY source of truth. No raw context is ever sent to the LLM.
        if not supporting_facts:
            print("⚠️ No supporting facts provided. Cannot generate grounded questions.")
            return {"questions": []}

        valid_questions = []

        # Process up to 3x requested count for filtering
        for fact_data in supporting_facts[:count * settings.FACT_MULTIPLIER]:
            if not isinstance(fact_data, dict):
                continue

            concept = fact_data.get("concept", "").strip()
            definition = fact_data.get("supporting_fact") or fact_data.get("definition") or fact_data.get("sentence") or ""

            if not concept or not definition:
                continue

            fill_result = self.fill_blank_generator.generate_fill_blank(
                topic,
                [fact_data]
            )

            question = (
                fill_result["questions"][0]
                if fill_result.get("questions")
                else None
            )

            # Fallback to MCQ if fill blank failed
            if question is None:
                question = self.generate_from_fact(
                    fact=definition,
                    answer=concept,
                    topic=topic,
                    fact_data=fact_data
                )

            if question:

                print("\n===== QUESTION TYPE =====")
                print(question.get("type"))
                print(question)

                if question.get("type", "mcq") != "fill_blank":

                    if not validate_structure(question):
                        print("FAILED: structure")
                        continue

                    if not validate_distractors(question):
                        print("FAILED: distractors")
                        continue

                    if not validate_semantic(question):
                        print("FAILED: semantic")
                        continue
                    if not validate_domain_correctness(
                        question,
                        concept,
                        definition,
                    ):
                        print("FAILED: domain")
                        continue

                if question:

                    print("\n===== QUESTION TYPE =====")
                    print(question.get("type"))
                    print(question)

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

        return {"questions": valid_questions}

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

        # =========================================================================
    # PRIVATE HELPERS
    # =========================================================================

    def _build_fill_blank_prompt(self, definition: str, concept: str, topic: str) -> str:
        """
        Build a prompt for fill-in-the-blank question using the extracted fact.

        Args:
            definition: The supporting fact
            concept: The correct answer/concept
            topic: The topic name

        Returns:
            Prompt string for the LLM
        """
        safe_topic = str(topic).strip() if topic else "Unknown"

        return f"""You are a computer science tutor creating a fill-in-the-blank question.

CONCEPT: {concept}
FACT: {definition}
TOPIC: {safe_topic}

Requirements:
1. The answer MUST be "{concept}" - this is non-negotiable.
2. Create a question where the student must fill in "{concept}" as the answer.
3. Use "_______" for the blank space.
4. The question must test understanding of "{concept}" based on the FACT provided.
5. Include a short explanation that references the FACT.

Example:
FACT: "Database normalization reduces redundancy."
CONCEPT: "redundancy"
QUESTION: "Database normalization reduces _______."
ANSWER: "redundancy"
EXPLANATION: "Normalization reduces redundancy in the database."

Now generate 1 fill-in-the-blank question where the answer is exactly "{concept}".

Return ONLY valid JSON in this format:
{{
  "questions": [
    {{
      "question": "Your question with _______ blank",
      "correct": "{concept}",
      "explanation": "Your explanation referencing the fact."
    }}
  ]
}}"""


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