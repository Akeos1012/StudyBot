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
import random
import logging
from typing import List, Dict, Any
from difflib import SequenceMatcher

from ..rag.metadata_loader import MetadataLoader
from ..rag.fact_extractor import FactExtractor
from ..quiz.quiz_generator import QuizGenerator

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

        notes = self._get_notes_for_topic(topic, subtopic)

        if not notes:
            logger.error(f"No notes found for topic: {topic}")
            return []

        ranked_notes = self._rank_notes_by_content(notes)

        extracted_facts = self._extract_facts_from_notes(ranked_notes, topic)

        questions = self._generate_from_facts(extracted_facts, topic, count)

        if len(questions) < count:
            logger.info("Not enough fact-based questions. Using fallback.")

            fallback_questions = self._generate_fallback_questions(
                ranked_notes, topic, count - len(questions)
            )

            questions.extend(fallback_questions)

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

        cache = self.quiz_generator.cache

        if fresh:
            logger.info(f"Clearing cache for {topic}")

            cache.invalidate_topic_cache(topic, subtopic, difficulty, question_type)

        pool = cache.get_pool(topic, subtopic, difficulty, question_type)

        if len(pool) < MIN_POOL_SIZE:

            logger.info(f"Pool size {len(pool)} is below minimum. Generating more.")

            new_questions = self.generate_questions_for_topic(
                topic, subtopic, difficulty
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

        if subtopic:

            notes = self.metadata_loader.get_notes_by_subtopic(topic, subtopic)

            if not notes:
                logger.warning(f"No notes found for {subtopic}. Falling back.")

                notes = self.metadata_loader.get_notes_by_topic(topic)

        else:

            notes = self.metadata_loader.get_notes_by_topic(topic)

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

        return questions

    def _generate_fallback_questions(
        self, notes: List[Dict[str, Any]], topic: str, target_count: int
    ) -> List[Dict[str, Any]]:

        questions = []

        max_attempts = target_count * 3

        top_notes = notes[:6] if len(notes) >= 6 else notes

        for _ in range(max_attempts):

            if len(questions) >= target_count:
                break

            if not top_notes:
                break

            selected = random.sample(top_notes, min(3, len(top_notes)))

            context_parts = []

            for meta in selected:

                content = self.metadata_loader.get_truncated_content(meta["path"], 2000)

                context_parts.append(f"# {meta['title']}\n{content}")

            context = "\n\n---\n\n".join(context_parts)

            result = self.quiz_generator.generate_questions(
                context=context, topic=topic, count=1
            )

            new_questions = result.get("questions", [])

            if new_questions:

                question = new_questions[0]

                if self._is_valid_question(question) and not self._is_duplicate(
                    question, questions
                ):
                    questions.append(question)

        return questions

    def _is_valid_question(self, question: Dict[str, Any]) -> bool:

        options = " ".join(question.get("options", []))

        return "Option 1" not in options and "Option 2" not in options

    def _is_duplicate(
        self, question: Dict[str, Any], existing: List[Dict[str, Any]]
    ) -> bool:

        current = question.get("question", "").lower()

        for item in existing:

            previous = item.get("question", "").lower()

            similarity = SequenceMatcher(None, current, previous).ratio()

            if similarity > 0.6:
                return True

        return False
