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
- Fact extraction (fact_extractor.py)
- Question generation (quiz_generator.py)
"""

import random
import logging
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher

from ..rag.metadata_loader import MetadataLoader
from ..rag.fact_extractor import FactExtractor
from ..quiz.quiz_generator import QuizGenerator, is_relevant_to_topic

logger = logging.getLogger(__name__)


class QuizService:
    """
    Service for generating and managing quizzes.

    Usage:
        service = QuizService(metadata_loader)
        questions = service.generate_questions("Cloud", count=3)
    """

    def __init__(self, metadata_loader: MetadataLoader,
                 min_pool_size: int = 15,
                 max_facts_per_note: int = 10,
                 max_notes_for_context: int = 3):
        """
        Initialize the quiz service.

        Args:
            metadata_loader: MetadataLoader instance
            min_pool_size: Minimum pool size before generating more
            max_facts_per_note: Max facts to extract per note
            max_notes_for_context: Max notes to use for context
        """
        self.metadata_loader = metadata_loader
        self.min_pool_size = min_pool_size
        self.max_facts_per_note = max_facts_per_note
        self.max_notes_for_context = max_notes_for_context

    def generate_questions_for_topic(self, topic: str, subtopic: str = "",
                                     difficulty: str = "medium",
                                     count: int = 15) -> List[Dict[str, Any]]:
        """
        Generate new questions for a topic to fill the pool.

        Args:
            topic: The topic name
            subtopic: Optional subtopic
            difficulty: Question difficulty
            count: Number of questions to generate

        Returns:
            List of generated questions
        """
        logger.info(f"Generating {count} new questions for {topic}...")

        # Get metadata
        notes = self._get_notes_for_topic(topic, subtopic)

        if not notes:
            logger.error(f"No notes found for topic: {topic}")
            return []

        # Rank notes
        ranked_notes = self._rank_notes_by_content(notes)

        # Extract facts
        extracted_facts = self._extract_facts_from_notes(ranked_notes, topic)

        # Generate questions from facts
        questions = self._generate_from_facts(extracted_facts, topic, count)

        # If not enough, use fallback
        if len(questions) < count:
            logger.info(f"Only got {len(questions)} questions from facts, using fallback...")
            fallback_questions = self._generate_fallback_questions(
                ranked_notes, topic, count - len(questions)
            )
            questions.extend(fallback_questions)

        logger.info(f"Generated {len(questions)} questions for {topic}")
        return questions[:count]

    def get_or_generate_questions(self, topic: str, subtopic: str = "",
                                  difficulty: str = "medium",
                                  count: int = 3,
                                  fresh: bool = False,
                                  question_type: str = "multiple") -> List[Dict[str, Any]]:
        """
        Get questions from cache or generate new ones.

        Args:
            topic: The topic name
            subtopic: Optional subtopic
            difficulty: Question difficulty
            count: Number of questions to return
            fresh: If True, clear cache before generating
            question_type: Type of questions ("multiple" or "fillblank")

        Returns:
            List of questions
        """
        generator = QuizGenerator()

        # Clear cache if fresh
        if fresh:
            logger.info(f"Fresh requested - clearing pool for {topic}")
            generator.cache.invalidate_topic_cache(topic, subtopic, difficulty, question_type)

        # Get current pool
        pool = generator.cache.get_pool(topic, subtopic, difficulty, question_type)

        # Generate more if pool is small
        if len(pool) < self.min_pool_size:
            logger.info(f"Pool too small ({len(pool)} questions), generating more...")
            new_questions = self.generate_questions_for_topic(topic, subtopic, difficulty)

            if new_questions:
                # Filter out fallback questions for cache
                real_questions = [q for q in new_questions if not q.get('_is_fallback', False)]
                if real_questions:
                    added = generator.cache.add_to_pool(
                        topic, subtopic, difficulty, question_type, real_questions
                    )
                    logger.info(f"Added {added} real questions to pool")
                pool = generator.cache.get_pool(topic, subtopic, difficulty, question_type)

        # Sample from pool
        sampled = generator.cache.sample(topic, subtopic, difficulty, question_type, count)
        return sampled or pool[:count]

    # =========================================================================
    # PRIVATE HELPERS
    # =========================================================================

    def _get_notes_for_topic(self, topic: str, subtopic: str) -> List[Dict[str, Any]]:
        """Get notes for a topic or subtopic."""
        if subtopic:
            notes = self.metadata_loader.get_notes_by_subtopic(topic, subtopic)
            if not notes:
                logger.warning(f"No notes found for subtopic '{subtopic}', falling back to topic")
                notes = self.metadata_loader.get_notes_by_topic(topic)
        else:
            notes = self.metadata_loader.get_notes_by_topic(topic)
        return notes

    def _rank_notes_by_content(self, notes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank notes by content length (highest first)."""
        return sorted(notes, key=lambda x: x.get("content_length", 0), reverse=True)

    def _extract_facts_from_notes(self, notes: List[Dict[str, Any]],
                                  topic: str) -> List[Dict[str, Any]]:
        """Extract facts from top notes."""
        fact_extractor = FactExtractor()
        extracted_facts = []

        for meta in notes[:self.max_notes_for_context]:
            content = self.metadata_loader.get_truncated_content(meta["path"], 2000)
            facts = fact_extractor.extract_facts(content, topic, source=meta["path"])
            extracted_facts.extend(facts)

        return extracted_facts

    def _generate_from_facts(self, facts: List[Dict[str, Any]],
                             topic: str, target_count: int) -> List[Dict[str, Any]]:
        """Generate questions from extracted facts."""
        generator = QuizGenerator()
        questions = []

        for fact_data in facts[:self.max_facts_per_note]:
            if len(questions) >= target_count:
                break

            fact = fact_data.get("statement", "")
            answer = fact_data.get("answer", "")

            if not fact or not answer:
                continue

            question = generator.generate_with_retry(fact, answer, topic, fact_data=fact_data)
            if question:
                questions.append(question)

        return questions

    def _generate_fallback_questions(self, notes: List[Dict[str, Any]],
                                     topic: str, target_count: int) -> List[Dict[str, Any]]:
        """Generate fallback questions when fact extraction fails."""
        generator = QuizGenerator()
        questions = []

        max_attempts = target_count * 3
        top_notes = notes[:6] if len(notes) >= 6 else notes

        for attempt in range(max_attempts):
            if len(questions) >= target_count:
                break

            num_notes = min(3, len(top_notes))
            selected_meta = random.sample(top_notes, num_notes)

            context_parts = []
            for meta in selected_meta:
                content = self.metadata_loader.get_truncated_content(meta["path"], 2000)
                context_parts.append(f"# {meta['title']}\n{content}")

            context = "\n\n---\n\n".join(context_parts)

            result = generator.generate_questions(context=context, topic=topic, count=1)
            new_questions = result.get("questions", [])

            if new_questions:
                q = new_questions[0]
                if self._is_valid_question(q) and not self._is_duplicate(q, questions):
                    questions.append(q)

        return questions

    def _is_valid_question(self, question: Dict[str, Any]) -> bool:
        """Check if a question is valid."""
        options_text = ' '.join(question.get('options', []))
        if 'Option 1' in options_text or 'Option 2' in options_text:
            return False
        return True

    def _is_duplicate(self, question: Dict[str, Any],
                      existing: List[Dict[str, Any]]) -> bool:
        """Check if a question is a duplicate."""
        q_text = question.get('question', '')
        for existing_q in existing:
            existing_text = existing_q.get('question', '')
            ratio = SequenceMatcher(None, q_text.lower(), existing_text.lower()).ratio()
            if ratio > 0.6:
                return True
        return False