import json
import re
import time
from difflib import SequenceMatcher
from json_repair import repair_json
from typing import List, Dict, Any, Optional, Tuple

from .question_cache import QuestionCache
from .question_scorer import QuestionScorer
from .question_similarity import is_similar_to_pool
from .question_prompt import build_fact_question_prompt
from .explanation_validator import validate_explanation
from ..rag.fact_cache import FactCache
from .llm_parser import LLMParser
from .llm_client import LLMClient
import traceback
from app.utils.performance_profiler import profile_time

from .question_semantic import (
    validate_semantic,
    has_garbled_text,
)

from .validation_logger import log_validation_failure

from .options_parser import (
    normalize_options,
    get_correct_text_from_options,
)

from .question_grounding import (
    validate_grounding,
    normalize_supporting_fact,
    attach_grounding_fields,
    select_supporting_fact,
    question_equals_answer,
)

from .question_validator import (
    validate_structure,
    normalize_and_validate_correct_field,
    validate_question_focus,
    is_relevant_to_topic,
    is_valid_concept,
    is_duplicate_question,
)

from .domain_validator import validate_domain_correctness
from ..rag.fact_cleaner import clean_text
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

# Maximum number of facts to process per generation request
MAX_FACTS_PER_REQUEST = 30

# Minimum quality score for a question to be accepted
MIN_QUALITY_SCORE = 0.6

# Similarity threshold for duplicate detection
SIMILARITY_THRESHOLD = 0.90

# Default number of attempts for retry
DEFAULT_MAX_ATTEMPTS = 3

# Default LLM model
DEFAULT_MODEL = "qwen2.5:3b"


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
            question = self.generate_from_fact(
                fact,
                answer,
                topic,
                fact_data
            )
            if question:
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

            # Format options immediately
            options = question.get('options', [])
            if options:
                question['options'] = normalize_options(options)

            # ===== VALIDATION PIPELINE =====

            # Stage 1: Structure
            if not validate_structure(question):
                log_validation_failure(question, "structure", "Structure validation failed")
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

            # Stage 3: Semantic
            if not validate_semantic(question):
                log_validation_failure(question, "semantic", "Semantic validation failed")
                return None

            # Stage 4: Domain correctness
            if not validate_domain_correctness(question):
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
            facts = self.retriever.retrieve(topic=topic, limit=20)
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
        for fact_data in supporting_facts[:count * 3]:
            if not isinstance(fact_data, dict):
                continue

            concept = fact_data.get("concept") or fact_data.get("answer") or ""
            definition = fact_data.get("supporting_fact") or fact_data.get("definition") or fact_data.get("sentence") or ""

            if not concept or not definition:
                continue

            # Use the proven fact-based generation pipeline
            question = self.generate_from_fact(
                fact=definition,
                answer=concept,
                topic=topic,
                fact_data=fact_data
            )

            if question:
                valid_questions.append(question)
                if len(valid_questions) >= count:
                    break

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
        Generate grounded fill-in-the-blank questions from extracted facts.

        Args:
            topic: The topic name
            supporting_facts: List of extracted fact dictionaries

        Returns:
            Dictionary with 'questions' key containing list of validated questions
        """
        self._supporting_facts = supporting_facts or []

        # ===== HALLUCINATION PREVENTION =====
        # Facts are the ONLY source of truth. No raw context is ever sent to the LLM.
        if not supporting_facts:
            print("⚠️ No supporting facts provided. Cannot generate grounded fill-in-the-blank questions.")
            return {"questions": []}

        valid_questions = []

        for fact_data in supporting_facts[:5]:  # Try up to 5 facts
            if not isinstance(fact_data, dict):
                continue

            concept = fact_data.get("concept") or fact_data.get("answer") or ""
            definition = fact_data.get("supporting_fact") or fact_data.get("definition") or fact_data.get("sentence") or ""

            if not concept or not definition:
                continue

            # Build prompt using the extracted fact
            prompt = self._build_fill_blank_prompt(definition, concept, topic)

            try:
                start_time = time.time()
                content = self.llm.generate(
                    prompt,
                    temperature=0.3,
                    top_p=0.7,
                    num_predict=800
                )
                self._record_llm_usage(content, time.time() - start_time)

                print(f"Fill-blank response received: {len(content)} characters")

                json_match = re.search(r'\{[\s\S]*\}', content)
                if not json_match:
                    continue

                content = json_match.group()
                content = content.replace('```json', '').replace('```', '').strip()

                try:
                    repaired = repair_json(content)
                    result = json.loads(repaired)
                except Exception as e:
                    print(f"⚠️ Fill-blank JSON repair failed: {e}")
                    continue

                if 'questions' not in result:
                    continue

                for q in result['questions']:
                    if 'question' in q and 'correct' in q and '_______' in q['question']:
                        # Validate: correct answer must match the concept
                        if q['correct'].lower() == concept.lower():
                            # Attach grounding fields
                            q['supporting_fact'] = definition
                            q['concept'] = concept
                            q['source_note'] = fact_data.get('source_note', 'inline')
                            q['fact_id'] = fact_data.get('fact_id', f"fillblank_{concept.lower().replace(' ', '_')}")
                            q['_quality_score'] = 0.7  # Default quality for fill-blank

                            valid_questions.append(q)
                            print(f"✅ Fill-blank question generated and grounded for '{concept}'")
                        else:
                            print(f"⚠️ Fill-blank answer mismatch: got '{q['correct']}', expected '{concept}'")
                            continue

                if valid_questions:
                    break

            except Exception as e:
                print(f"Error generating fill-blank: {e}")
                continue

        self._generated_questions.extend(valid_questions)

        return {"questions": valid_questions}

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