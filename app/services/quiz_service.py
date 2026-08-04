# app/services/quiz_service.py
# =====================================================
# PIPELINE CHECKPOINT: SERVICE ORCHESTRATION LAYER
#
# Position:
#
# API Route
#      ↓
# QuizService
#      ↓
# MetadataLoader
#      ↓
# FactExtractor
#      ↓
# GroundingProcessor
#      ↓
# QuizGenerator
#      ↓
# Question Cache
#
# Purpose:
# Coordinates the quiz generation workflow.
#
# Responsibilities:
# - Retrieve notes
# - Rank relevant notes
# - Extract facts
# - Ground extracted knowledge
# - Request question generation
# - Manage question pool/cache
# - Collect performance metrics
#
# Connected Modules:
#
# Called by:
#   - app/api/routes.py
#
# Uses:
#   - app/rag/metadata_loader.py
#   - app/rag/fact_extractor.py
#   - app/rag/grounding_processor.py
#   - app/quiz/quiz_generator.py
#   - app/quiz/question_cache.py
#   - app/monitoring/quiz_metrics.py
#
# IMPORTANT RULES:
#
# - This layer coordinates only.
# - Do not add validation rules here.
# - Do not allow LLM output to modify facts.
# - Facts remain the source of truth.
# - Generation failures should return safely.
#
# Risk:
# Changing flow order can break grounding,
# caching behavior, or metric tracking.
# =====================================================

import time
import logging
import random
from datetime import datetime
from typing import List, Dict, Any, Optional

from ..rag.grounding_processor import GroundingProcessor
from ..learning.analytics.analytics_repository import AnalyticsRepository
from ..rag.metadata_loader import MetadataLoader
from ..rag.fact_extractor import FactExtractor
from ..quiz.quiz_generator import QuizGenerator
from app.services.quiz_session_service import QuizSessionService
from ..quiz.pool_manager import PoolManager
from ..monitoring.quiz_metrics import QuizMetrics
from ..monitoring.metrics_context import MetricsContext
from ..quiz.question_metadata import update_answer_result
from app.models.user_context import UserContext
from app.models.quiz_session import QuizSession, SessionStatus
from app.learning.mastery_service import MasteryService
from app.learning.history_service import HistoryService
from app.learning.analytics_service import LearningAnalyticsService
from app.learning.recommendation_engine import RecommendationEngine
from app.utils.question_id import generate_question_id

# ...


from ..monitoring.performance_monitor import PerformanceMonitor
from app.config import settings

logger = logging.getLogger(__name__)
POOL_REFILL_AMOUNT = 10


class QuizService:
    """
    CHECKPOINT:
    Quiz pipeline controller

    Receives:
        Topic request
        Difficulty
        Question count
        Question type

    Returns:
        Generated validated quiz questions

    Pipeline:

        Notes
          ↓
        Facts
          ↓
        Grounding
          ↓
        Question Generation
          ↓
        Cache Pool
          ↓
        Response

    Connected:
        MetadataLoader
            ↓
        FactExtractor
            ↓
        GroundingProcessor
            ↓
        QuizGenerator

    Must not:
        - Create facts
        - Rewrite source knowledge
        - Contain LLM prompts
        - Replace validators

    Risk:
        Changes here affect the entire quiz workflow.
    """

    def __init__(
        self,
        metadata_loader,
        quiz_generator,
        pool_manager,
        mastery_service,
        history_service,
        analytics_service,
        recommendation_engine,
        quiz_session_service,
        analytics_repository=None,
    ):
        self.metadata_loader = metadata_loader
        self.quiz_generator = quiz_generator
        self.pool_manager = pool_manager
        self.mastery_service = mastery_service
        self.history_service = history_service
        self.analytics_service = analytics_service
        self.recommendation_engine = recommendation_engine
        self.quiz_session_service = quiz_session_service
        self.analytics_repository = analytics_repository

    def create_quiz_session(
        self,
        user_id: str,
        topic: str,
        difficulty: str = "medium",
        count: int = 3,
        fresh: bool = False,
        adaptive: bool = False,
    ) -> QuizSession:
        questions = self.get_or_generate_questions(
            topic=topic,
            difficulty=difficulty,
            count=count,
            fresh=fresh,
            adaptive=adaptive,
            user_context=UserContext(user_id=user_id),
        )
        
        question_ids = [q["question_id"] for q in questions]
        session = self.quiz_session_service.create_session(
            user_id=user_id, topic=topic, difficulty=difficulty, question_ids=question_ids
        )
        
        # Inject session_id into questions
        for q in questions:
            q.setdefault("metadata", {})["session_id"] = session.session_id
            
        return session

    def generate_questions_for_topic(
        self,
        topic: str,
        subtopic: str = "",
        difficulty: str = "medium",
        count: int = 15,
        user_context: Optional[UserContext] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate questions for a topic.
        """
        logger.info(f"Generating {count} questions for topic: {topic}")

        metrics = QuizMetrics(topic=topic)
        metrics_context = MetricsContext(quiz_metrics=metrics, topic=topic)

        metrics.questions_requested = count
        overall_start = time.perf_counter()

        stage = time.perf_counter()
        notes = self._get_notes_for_topic(topic, subtopic)
        metrics.notes_loaded = len(notes)

        logger.info(
            "PROFILE | Note retrieval: %.3fs",
            time.perf_counter() - stage,
        )

        if not notes:
            logger.error(f"No notes found for topic: {topic}")
            metrics.add_failure("generation_failed_no_notes")
            return []

        stage = time.perf_counter()
        ranked_notes = self._rank_notes_by_content(notes)
        logger.info(
            "PROFILE | Note ranking: %.3fs",
            time.perf_counter() - stage,
        )

        stage = time.perf_counter()
        extracted_facts = self._extract_facts_from_notes(ranked_notes, topic)
        metrics.facts_extracted = len(extracted_facts)
        if not extracted_facts:
            logger.error(f"No facts extracted for topic: {topic}")
            metrics.add_failure("generation_failed_no_facts_extracted")
            return []
        logger.info(
            "PROFILE | Fact extraction: %.3fs",
            time.perf_counter() - stage,
        )

        stage = time.perf_counter()
        questions = self._generate_from_facts(
            extracted_facts, topic, count, "multiple", metrics_context=metrics_context
        )

        logger.info(
            "PROFILE | Question generation: %.3fs",
            time.perf_counter() - stage,
        )

        if len(questions) < count:
            logger.warning(
                "Only generated %d of %d requested questions.",
                len(questions),
                count,
            )

        metrics.questions_generated = len(questions)

        logger.info(
            "PROFILE | TOTAL generate_questions_for_topic: %.3fs",
            time.perf_counter() - overall_start,
        )

        metrics.questions_accepted = min(
            len(questions),
            count,
        )

        metrics.questions_rejected = max(
            0,
            metrics.questions_generated - metrics.questions_accepted,
        )

        for q in questions:
            q["topic"] = topic
            q["subtopic"] = subtopic
            q["question_id"] = generate_question_id(q.get("question", ""))

        for q in questions:
            q["difficulty"] = difficulty

            if q.get("type") == "fill_blank":
                q["question_type"] = "fillblank"
            else:
                q["question_type"] = "multiple"
        return questions[:count]

    def get_or_generate_questions(
        self,
        topic: str,
        subtopic: str = "",
        difficulty: str = "medium",
        count: int = 3,
        fresh: bool = False,
        question_type: str = "multiple",
        user_context: Optional[UserContext] = None,
        adaptive: bool = False,
        personalize: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve questions from cache or generate new ones.
        """
        start_time = time.time()

        # Adaptive difficulty logic
        if adaptive and user_context and user_context.user_id:
            recommended_difficulty = self.mastery_service.get_recommended_difficulty(
                user_context, topic
            )
            if recommended_difficulty:
                logger.info(
                    f"Adaptive difficulty active: overriding {difficulty} with {recommended_difficulty}"
                )
                difficulty = recommended_difficulty

        logger.info("Generating quiz | topic=%s fresh=%s count=%s", topic, fresh, count)

        performance_monitor = PerformanceMonitor()
        performance_monitor.start()

        cache = self.quiz_generator.cache

        concept_weights = None
        if personalize and user_context and user_context.user_id:
            summary = self.analytics_service.get_learning_summary(user_context, topic)
            concept_weights = self.recommendation_engine.get_concept_weights(summary)

        if fresh:
            logger.info(f"Clearing cache for {topic}")
            cache.invalidate_topic_cache(topic, subtopic, difficulty, question_type)

        if question_type == "fillblank":
            return self.generate_fill_blank_questions(
                topic=topic, subtopic=subtopic, difficulty=difficulty, count=count
            )

        # Proactive Pool Management
        try:
            health = self.pool_manager.should_expand_pool(topic)
            if health.get("expand", False):
                logger.info(f"Pool expansion triggered: {health.get('reasons')}")
                self.pool_manager.expand_pool(topic)
        except Exception as e:
            logger.error(f"PoolManager expansion failed for {topic}: {e}")
            # Continue to fallback generation

        if not fresh:
            cached_questions = cache.sample(
                topic,
                subtopic,
                difficulty,
                question_type,
                count,
                concept_weights=concept_weights,
            )
            if cached_questions and len(cached_questions) >= count:
                logger.info(
                    "Serving %d cached questions from pool for topic '%s'",
                    len(cached_questions),
                    topic,
                )
                return cached_questions

        # Generate fresh questions if cache bypass requested or pool is depleted
        logger.info(
            "Generating fresh questions for topic '%s' (fresh=%s)", topic, fresh
        )

        new_questions = self.generate_questions_for_topic(
            topic,
            subtopic,
            difficulty,
            max(count, POOL_REFILL_AMOUNT),
            user_context=user_context,
        )

        real_questions = [q for q in new_questions if not q.get("_is_fallback", False)]

        if real_questions:

            added = 0

            for q in real_questions:
                q_type = q.get("question_type", "multiple")

                result = cache.add_to_pool(topic, subtopic, difficulty, q_type, [q])

                if result:
                    added += result

            logger.info("Added %s new questions into pool", added)

        # Return only new questions
        result = real_questions[:count]

        performance_data = performance_monitor.stop()

        # Define metrics context if not already available
        metrics = QuizMetrics(topic=topic)
        metrics_context = MetricsContext(quiz_metrics=metrics, topic=topic)

        if metrics_context and metrics_context.quiz_metrics:
            metrics = metrics_context.quiz_metrics
            metrics.record_cpu(performance_data["cpu_usage_percent"])

            metrics.record_ram(performance_data["ram_usage_percent"])

            metrics.record_gpu(performance_data["gpu_usage_percent"])

            metrics.record_gpu_memory(performance_data["gpu_memory_used_mb"])

            metrics.record_gpu_temperature(performance_data["gpu_temperature_c"])

            logger.info("Quiz metrics: %s", metrics.report())

        logger.info("Quiz generation completed in %.2fs", time.time() - start_time)

        for q in result:
            q["topic"] = topic
            q["subtopic"] = subtopic
            q["question_id"] = generate_question_id(q.get("question", ""))

        return result

    def submit_session_answer(
        self, session_id: str, question_id: str, answer: str, user_context: UserContext
    ) -> Dict[str, Any]:
        session = self.quiz_session_service.get_session(session_id)
        if not session or session.status != SessionStatus.ACTIVE:
            raise ValueError("Invalid or inactive session")
        
        # Ensure question belongs to session
        if question_id not in session.question_ids:
            raise ValueError("Question not part of session")
            
        result = self.record_answer(question_id, answer, user_context)
        
        # Update session position if needed (simplified)
        session.current_question_index += 1
        self.quiz_session_service.update_progress(session_id, session.current_question_index)
        
        return result

    def get_knowledge_summary(self) -> Dict[str, Any]:
        """
        Aggregate topic data for the Knowledge Library UI.
        """
        topics = self.metadata_loader.get_all_topics()
        summary = []
        
        # Ensure fact cache is loaded (might be lazy initialized in tests/prod)
        if not self.quiz_generator.fact_cache.cache:
            self.quiz_generator.fact_cache.load()
            
        # Get metadata file modification time for last_updated
        last_updated = datetime.now().isoformat() # Default
        if self.metadata_loader.metadata_file.exists():
            last_updated = datetime.fromtimestamp(
                self.metadata_loader.metadata_file.stat().st_mtime
            ).isoformat()
            
        for topic in topics:
            notes = self.metadata_loader.get_notes_by_topic(topic)
            facts = self.quiz_generator.fact_cache.get_facts(topic)
            
            summary.append({
                "name": topic,
                "note_count": len(notes),
                "fact_count": len(facts),
                "last_updated": last_updated,
                "status": "ready"
            })
            
        return {"topics": summary, "total_topics": len(summary)}

    def record_answer(
        self,
        question_id: str,
        answer: str,
        user_context: Optional[UserContext] = None,
    ):
        cache = self.quiz_generator.cache

        question = cache.get_question_by_id(question_id)

        if not question:
            return {
                "success": False,
                "question_id": question_id,
                "correct": False,
                "success_rate": 0.0,
            }

        correct = answer.upper() == question.get("correct", "").upper()

        update_answer_result(question["metadata"], correct)

        cache.update_question(question_id, question)

        # Update mastery
        if user_context and user_context.user_id:
            concept = question.get("concept") or question.get("topic", "General")
            self.mastery_service.update_mastery(user_context, concept, correct)
            repository = self.analytics_repository
            if (
                repository is None
                and hasattr(self.analytics_service, "repository")
                and isinstance(self.analytics_service.repository, AnalyticsRepository)
            ):
                repository = self.analytics_service.repository
            if repository is not None:
                # MANDATORY: Extract session_id from question metadata
                session_id = question.get("metadata", {}).get("session_id")
                if not session_id:
                    logger.warning(f"Answer recorded without session_id for question {question_id}")
                    # For now keep existing behavior, but log it
                    session_id = user_context.user_id

                repository.record_learning_event(
                    user_id=user_context.user_id,
                    session_id=session_id,
                    event_type="answer",
                    topic=question.get("topic", "General"),
                    concept=concept,
                    correct=correct,
                    difficulty=question.get("difficulty"),
                    response_time_ms=question.get("metadata", {}).get(
                        "response_time_ms"
                    ),
                )

        return {
            "success": True,
            "question_id": question_id,
            "correct": correct,
            "success_rate": question["metadata"]["success_rate"],
        }

    # ============================================================
    # PRIVATE HELPERS
    # ============================================================

    def generate_fill_blank_questions(
        self,
        topic: str,
        subtopic: str = "",
        difficulty: str = "medium",
        count: int = 3,
    ):
        """
        Generate fill-in-the-blank questions.
        """

        notes = self._get_notes_for_topic(topic, subtopic)

        if not notes:
            return []

        ranked_notes = self._rank_notes_by_content(notes)

        facts = self._extract_facts_from_notes(ranked_notes, topic)

        result = self.quiz_generator.generate_fill_blank(
            topic=topic, supporting_facts=facts
        )

        return result.get("questions", [])[:count]

    """
    FUNCTION CHECKPOINT:
    DATA CHECKPOINT

    Stage:
        Topic Request
            ↓
        Note Retrieval

    Input:
        Topic and optional subtopic

    Output:
        Markdown note metadata

    Used before:
        Fact extraction

    Must preserve:
        - Source path
        - Note content reference

    Must not:
        - Modify note content
        - Generate knowledge
    """

    def _get_notes_for_topic(self, topic: str, subtopic: str) -> List[Dict[str, Any]]:
        topic_aliases = {
            "cloud computing": "Cloud",
        }

        normalized_topic = topic_aliases.get(topic.lower(), topic)

        if subtopic:
            notes = self.metadata_loader.get_notes_by_subtopic(
                normalized_topic, subtopic
            )
            if not notes:
                logger.warning(f"No notes found for {subtopic}. Falling back.")
                notes = self.metadata_loader.get_notes_by_topic(normalized_topic)
        else:
            notes = self.metadata_loader.get_notes_by_topic(normalized_topic)

        return notes

    def _rank_notes_by_content(
        self, notes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return sorted(notes, key=lambda x: x.get("content_length", 0), reverse=True)

    """
    FUNCTION CHECKPOINT:
    DATA CHECKPOINT

    Stage:

        Raw Notes
            ↓
        FactExtractor
            ↓
        GroundingProcessor
            ↓
        Valid Facts

    Input:
        Retrieved notes

    Output:
        Grounded fact objects

    Connected:
        FactExtractor
            ↓
        GroundingProcessor

    IMPORTANT:
        Facts are the source of truth.

    Must not:
        - Invent missing facts
        - Expand concepts beyond notes
        - Let generated questions modify facts
    """

    def _extract_facts_from_notes(
        self, notes: List[Dict[str, Any]], topic: str
    ) -> List[Dict[str, Any]]:

        # ------------------------------------------------------------------
        # Issue #1 fix: use the pre-built FactCache loaded at startup.
        # QuizGenerator owns a FactCache that is fully loaded when the app
        # starts.  Re-extracting facts from disk on every request was
        # bypassing it entirely and causing unnecessary I/O + latency.
        # Fall back to live extraction only when the cache is empty.
        # ------------------------------------------------------------------
        cached_facts = self.quiz_generator.fact_cache.get_facts(topic)
        if cached_facts:
            logger.info(
                "FactCache hit: returning %d pre-built facts for topic '%s'",
                len(cached_facts),
                topic,
            )
            return cached_facts

        logger.info(
            "FactCache miss for topic '%s' — falling back to live extraction",
            topic,
        )

        extractor = FactExtractor()
        grounder = GroundingProcessor()

        extracted = []

        # Notes debug disabled
        # print("\n===== NOTES DEBUG =====")
        # print(type(notes))
        # print(type(notes[0]))
        # pprint(notes[0])
        # print("=======================\n")

        for note in notes:
            source = note["path"]

            content = self.metadata_loader.get_note_content(source)

            if not content:
                logger.warning(f"Could not load note: {source}")
                continue

            facts = extractor.extract_facts(
                content,
                topic,
                source=source,
            )

            grounded = grounder.ground_all(facts)

            extracted.extend(grounded)

        return extracted

    """
    FUNCTION CHECKPOINT:
    GENERATION CHECKPOINT

    Stage:

        Valid Facts
            ↓
        QuizGenerator
            ↓
        Questions

    Input:
        Grounded facts

    Output:
        Generated questions

    Connected:
        Fact data
            ↓
        QuizGenerator
            ↓
        Question Validator

    Must preserve:
        - Answer grounding
        - Fact relationship
        - Topic alignment

    Must not:
        - Accept unsupported answers
        - Replace source facts
        - Bypass validation
    """

    def _generate_from_facts(
        self,
        facts: List[Dict[str, Any]],
        topic: str,
        target_count: int,
        question_type: str = "multiple",
        metrics_context: Optional[MetricsContext] = None,
    ) -> List[Dict[str, Any]]:

        questions = []

        # ---------- Multiple Choice ----------
        for fact_data in facts[: settings.MAX_FACTS_PER_NOTE]:

            if len(questions) >= target_count:
                break

            fact = (
                fact_data.get("supporting_fact")
                or fact_data.get("definition")
                or fact_data.get("sentence")
                or ""
            )

            answer = fact_data.get("concept", "").strip()

            if not fact or not answer:
                continue

            llm_start = time.perf_counter()

            question = self.quiz_generator.generate_with_retry(
                fact,
                answer,
                topic,
                fact_data=fact_data,
                supporting_facts=facts,
                question_type=question_type,
                metrics_context=metrics_context,
            )

            llm_duration = time.perf_counter() - llm_start

            if metrics_context and metrics_context.quiz_metrics:
                metrics_context.quiz_metrics.record_llm_call(llm_duration)

            if question:
                questions.append(question)

                if metrics_context and metrics_context.quiz_metrics:
                    metrics_context.quiz_metrics.facts_used += 1
            else:
                if metrics_context and metrics_context.quiz_metrics:
                    metrics_context.quiz_metrics.add_failure(
                        "generation_failed_retry_exhaustion"
                    )

        # ---------- Fill Blank ----------
        fill_blank = self.quiz_generator.generate_fill_blank(
            topic=topic,
            supporting_facts=facts,
        )

        questions.extend(fill_blank.get("questions", []))
        logger.info(
            "MCQ generated: %s | Fill Blank generated: %s | Total before shuffle: %s",
            len(questions) - len(fill_blank.get("questions", [])),
            len(fill_blank.get("questions", [])),
            len(questions),
        )

        # ---------- Shuffle ----------
        random.shuffle(questions)

        return questions[:target_count]
