# app/services/quiz_service.py
"""
Quiz Service - Orchestrates quiz generation.

This service coordinates the quiz generation pipeline:
- Retrieving notes
- Extracting facts
- Generating questions
- Managing cache
- Formatting responses

This module is NOT responsible for:
- HTTP handling (main.py)
- Question validation rules
- LLM communication
- Prompt construction
"""

import time
import logging
from typing import List, Dict, Any

from ..rag.metadata_loader import MetadataLoader
from ..rag.fact_extractor import FactExtractor
from ..quiz.quiz_generator import QuizGenerator
from ..monitoring.quiz_metrics import QuizMetrics
from ..quiz.validation_logger import set_metrics, get_metrics
from ..config.quiz_config import (
    MIN_POOL_SIZE,
    MAX_FACTS_PER_NOTE,
    MAX_NOTES_FOR_CONTEXT,
)

logger = logging.getLogger(__name__)


class QuizService:
    """
    Service for generating and managing quizzes.

    The service coordinates existing components.
    It does not create QuizGenerator instances repeatedly.

    Usage:
        service = QuizService(
            metadata_loader,
            quiz_generator
        )

        questions = service.get_or_generate_questions(
            "Cloud Computing",
            count=3
        )
    """

    def __init__(self, metadata_loader: MetadataLoader, quiz_generator: QuizGenerator):
        self.metadata_loader = metadata_loader
        self.quiz_generator = quiz_generator

    def generate_questions_for_topic(
        self,
        topic: str,
        subtopic: str = "",
        difficulty: str = "medium",
        count: int = 15,
    ) -> List[Dict[str, Any]]:
        """
        Generate questions for a topic.
        """
        logger.info(f"Generating {count} questions for topic: {topic}")

        metrics = QuizMetrics(topic=topic)
        set_metrics(metrics)

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
        logger.info(
            "PROFILE | Fact extraction: %.3fs",
            time.perf_counter() - stage,
        )

        stage = time.perf_counter()
        questions = self._generate_from_facts(
            extracted_facts,
            topic,
            count,
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

        logger.info(
            "QUIZ METRICS: %s",
            metrics.report()
        )

        print("\n========== QUIZ METRICS ==========")
        print(metrics.report())

        return questions[:count]

    def get_or_generate_questions(
        self,
        topic: str,
        subtopic: str = "",
        difficulty: str = "medium",
        count: int = 3,
        fresh: bool = False,
        question_type: str = "multiple",
    ) -> List[Dict[str, Any]]:
        """
        Retrieve questions from cache or generate new ones.
        """
        start_time = time.time()
        print("\n========== QUIZ SERVICE ==========")
        print("Entered get_or_generate_questions()")
        print("Topic:", topic)
        print("Fresh:", fresh)
        print("Count:", count)
        print("==================================")

        cache = self.quiz_generator.cache

        if fresh:
            logger.info(f"Clearing cache for {topic}")
            cache.invalidate_topic_cache(topic, subtopic, difficulty, question_type)

        pool = cache.get_pool(topic, subtopic, difficulty, question_type)
        print("Pool size:", len(pool))

        if len(pool) < MIN_POOL_SIZE:
            print("Generating new questions...")
            logger.info(f"Pool size {len(pool)} is below minimum. Generating more.")

            new_questions = self.generate_questions_for_topic(
                topic, subtopic, difficulty, count  # Pass count to generate_questions_for_topic
            )

            real_questions = [
                q for q in new_questions if not q.get("_is_fallback", False)
            ]

            if real_questions:
                added = cache.add_to_pool(
                    topic, subtopic, difficulty, question_type, real_questions
                )
                logger.info(f"Added {added} questions to cache")

            pool = cache.get_pool(topic, subtopic, difficulty, question_type)

        sampled = cache.sample(topic, subtopic, difficulty, question_type, count)

        result = sampled or pool[:count]

        logger.info(f"Quiz generation completed in {time.time() - start_time:.2f}s")

        return result

    # ============================================================
    # PRIVATE HELPERS
    # ============================================================

    def _get_notes_for_topic(self, topic: str, subtopic: str) -> List[Dict[str, Any]]:
        topic_aliases = {
            "cloud computing": "Cloud",
        }

        normalized_topic = topic_aliases.get(topic.lower(), topic)

        if subtopic:
            notes = self.metadata_loader.get_notes_by_subtopic(
                normalized_topic,
                subtopic
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

    def _extract_facts_from_notes(
        self, notes: List[Dict[str, Any]], topic: str
    ) -> List[Dict[str, Any]]:
        extractor = FactExtractor()
        extracted = []

        for meta in notes[:MAX_NOTES_FOR_CONTEXT]:
            content = self.metadata_loader.get_truncated_content(meta["path"], 2000)
            facts = extractor.extract_facts(content, topic, source=meta["path"])
            extracted.extend(facts)

        return extracted

    def _generate_from_facts(
        self, facts: List[Dict[str, Any]], topic: str, target_count: int
    ) -> List[Dict[str, Any]]:
        questions = []

        for fact_data in facts[:MAX_FACTS_PER_NOTE]:
            if len(questions) >= target_count:
                break

            fact = fact_data.get("statement", "")
            answer = fact_data.get("answer", "")

            if not fact or not answer:
                continue

            question = self.quiz_generator.generate_with_retry(
                fact, answer, topic, fact_data=fact_data
            )

            if question:
                questions.append(question)

                metrics = get_metrics()
                if metrics:
                    metrics.facts_used += 1

        return questions