"""
Question Cache Module - Persistent storage layer for generated questions.

This module is responsible ONLY for storing, retrieving, and managing
cached question pools. It does NOT handle:
- Question validation (moved to question_validator.py)
- Duplicate/similarity detection (moved to question_similarity.py)
- Option/answer extraction (moved to options_parser.py)
- Quality scoring (moved to question_scorer.py)

All validation and deduplication logic is delegated to dedicated modules.
"""

import json
import hashlib
import random
from datetime import datetime
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from .question_validator import is_valid_question
from .question_similarity import is_similar_to_pool

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS
# ============================================================================

DEFAULT_CACHE_FILE = "question_cache.json"
DEFAULT_POOL_SIZE = 100
DEFAULT_USED_LIMIT = 100
MAX_POOL_SIZE_MULTIPLIER = 3

CACHE_VERSION = 1
CACHE_METADATA_KEY = "__metadata__"

# ============================================================================
# MAIN CLASS
# ============================================================================


class QuestionCache:
    """
    Persistent storage layer for generated questions.

    This class manages question pools in a JSON file. Each pool is keyed by
    a combination of topic, subtopic, difficulty, and question type.

    All validation and deduplication is delegated to separate modules.
    """

    def __init__(
        self, cache_file: str = DEFAULT_CACHE_FILE, pool_size: int = DEFAULT_POOL_SIZE
    ):
        """
        Initialize the question cache.

        Args:
            cache_file: Path to the cache JSON file
            pool_size: Maximum size for each question pool
        """
        self.cache_file = Path(cache_file)
        self.pool_size = pool_size
        self.cache = {}
        self._initialize_metadata()
        self.load_cache()

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def load_cache(self) -> None:
        """Load cache from disk."""
        if not self.cache_file.exists():
            self.cache = {}
            self._initialize_metadata()
            logger.info("No cache file found, starting with empty cache")
            return

        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                loaded = json.load(f)

            # Validate metadata
            metadata = loaded.get(CACHE_METADATA_KEY, {})
            version = metadata.get("version", 0)

            if version != CACHE_VERSION:
                logger.warning(
                    f"Cache version mismatch (v{version} != v{CACHE_VERSION}), rebuilding cache"
                )
                self.cache = {}
                self._initialize_metadata()
                return

            self.cache = loaded
            total_questions = self._total_questions()
            logger.info(
                f"Loaded {total_questions} cached questions across {len(self.cache)} pools"
            )

        except json.JSONDecodeError as e:
            logger.error(f"Corrupt cache file: {e}, resetting cache")
            self.cache = {}
            self._initialize_metadata()
        except Exception as e:
            logger.error(f"Could not load cache: {e}")
            self.cache = {}

    def save_cache(self) -> None:
        """Save cache to disk."""
        try:
            # Update metadata before saving
            self._update_metadata()

            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)

            total_questions = self._total_questions()
            logger.info(
                f"Saved {total_questions} questions across {len(self.cache)} pools"
            )

        except Exception as e:
            logger.error(f"Could not save cache: {e}")

    def get_key(
        self,
        topic: str,
        subtopic: str = "",
        difficulty: str = "medium",
        qtype: str = "multiple",
    ) -> str:
        """
        Generate a cache key from parameters.

        Args:
            topic: The topic name
            subtopic: Optional subtopic
            difficulty: Question difficulty
            qtype: Question type

        Returns:
            MD5 hash of the combined key string
        """
        key_str = f"{topic}_{subtopic}_{difficulty}_{qtype}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def get_pool(
        self,
        topic: str,
        subtopic: str = "",
        difficulty: str = "medium",
        qtype: str = "multiple",
    ) -> List[Dict[str, Any]]:
        """
        Get the full stored pool for a topic.

        Args:
            topic: The topic name
            subtopic: Optional subtopic
            difficulty: Question difficulty
            qtype: Question type

        Returns:
            List of valid questions in the pool
        """
        key = self.get_key(topic, subtopic, difficulty, qtype)
        pool = self.cache.get(key, [])

        # Filter out invalid questions
        valid_pool = [q for q in pool if is_valid_question(q)]

        # Clean up invalid questions
        if len(valid_pool) != len(pool):
            self.cache[key] = valid_pool
            self.save_cache()
            removed = len(pool) - len(valid_pool)
            logger.info(f"Removed {removed} invalid cached questions for {topic}")

        return valid_pool

    def add_to_pool(
        self,
        topic: str,
        subtopic: str,
        difficulty: str,
        qtype: str,
        new_questions: List[Dict[str, Any]],
    ) -> None:
        """
        Add new questions to the pool.

        Validation and deduplication are delegated to separate modules.

        Args:
            topic: The topic name
            subtopic: Optional subtopic
            difficulty: Question difficulty
            qtype: Question type
            new_questions: List of questions to add
        """
        if not new_questions:
            return

        key = self.get_key(topic, subtopic, difficulty, qtype)
        existing = self.cache.get(key, [])

        # Filter valid questions only

        for q in new_questions:
            q.setdefault(
                "cached_at",
                datetime.now().isoformat()
            )

        valid_new = []

        for q in new_questions:
            valid = is_valid_question(q)

            if not valid:
                logger.warning(
                    "Rejected invalid cached question: %s",
                    q.get("question", "")[:80]
                )

            if valid:
                valid_new.append(q)

        if not valid_new:
            logger.warning("No valid questions to add to pool")
            return

        # Deduplicate against existing pool
        unique_questions = self._deduplicate_questions(valid_new, existing)

        if not unique_questions:
            logger.info(f"No new unique questions to add to pool for {topic}")
            return

        # Add to pool
        existing.extend(unique_questions)

        # Cap pool size
        max_pool = self.pool_size * MAX_POOL_SIZE_MULTIPLIER
        if len(existing) > max_pool:
            # Keep the most recent questions (preserve order)
            existing = existing[-max_pool:]

        self.cache[key] = existing
        self.save_cache()

        logger.info(
            f"Added {len(unique_questions)} new questions to pool for {topic} (pool size: {len(existing)})"
        )

        return len(unique_questions)

    def sample(
        self,
        topic: str,
        subtopic: str = "",
        difficulty: str = "medium",
        qtype: str = "multiple_choice",
        count: int = 3,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Randomly sample questions from the pool.

        Args:
            topic: The topic name
            subtopic: Optional subtopic
            difficulty: Question difficulty
            qtype: Question type
            count: Number of questions to sample

        Returns:
            List of sampled questions, or None if pool is too small
        """
        pool = self.get_pool(topic, subtopic, difficulty, qtype)

        if len(pool) < count:
            logger.info(
                f"Pool too small ({len(pool)} < {count}), caller should generate more"
            )
            return None


        unused = [
            q for q in pool
            if q.get("usage_count", 0) == 0
        ]


        if len(unused) >= count:
            selected = random.sample(
                unused,
                count
            )
        else:
            logger.info(
                "All questions used. Selecting least recently seen."
            )

            selected = sorted(
                pool,
                key=lambda q: q.get(
                    "last_seen",
                    ""
                )
            )[:count]


        for q in selected:
            q["usage_count"] = q.get(
                "usage_count",
                0
            ) + 1

            q["last_seen"] = datetime.now().isoformat()


        self.save_cache()

        return selected

    def get_pool_size(
        self,
        topic: str,
        subtopic: str = "",
        difficulty: str = "medium",
        qtype: str = "multiple_choice",
    ) -> int:
        """
        Get the current pool size.

        Args:
            topic: The topic name
            subtopic: Optional subtopic
            difficulty: Question difficulty
            qtype: Question type

        Returns:
            Number of valid questions in the pool
        """
        return len(self.get_pool(topic, subtopic, difficulty, qtype))

    def clear(self) -> None:
        """Clear all cache."""
        self.cache = {}
        self._initialize_metadata()
        self.save_cache()
        logger.info("All cache cleared")

    def invalidate_topic_cache(
        self,
        topic: str,
        subtopic: str = "",
        difficulty: str = "medium",
        qtype: str = "multiple",
    ) -> None:
        """
        Safely clear a specific topic pool.

        Delegates to clear_topic().
        """
        self.clear_topic(topic, subtopic, difficulty, qtype)

    def clear_topic(
        self,
        topic: str,
        subtopic: str = "",
        difficulty: str = "medium",
        qtype: str = "multiple",
    ) -> None:
        """
        Clear cache for a specific topic.

        Args:
            topic: The topic name
            subtopic: Optional subtopic
            difficulty: Question difficulty
            qtype: Question type
        """
        key = self.get_key(topic, subtopic, difficulty, qtype)

        if key in self.cache:
            del self.cache[key]
            self.save_cache()
            logger.info(f"Cleared pool for topic: {topic} (subtopic: {subtopic})")
        else:
            logger.warning(f"No pool found for topic: {topic}")

    def get_pool_summary(self, topic: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a summary of the pool for debugging.

        Args:
            topic: Optional topic name. If provided, returns summary for that topic.
                  If None, returns overall summary.

        Returns:
            Dictionary with pool summary information
        """
        if topic:
            key = self.get_key(topic, "", "medium", "multiple")
            pool = self.cache.get(key, [])
            return {
                "topic": topic,
                "pool_size": len(pool),
                "questions": [q.get("question", "")[:50] + "..." for q in pool[:5]],
            }
        else:
            return {
                "total_pools": len(self.cache) - 1,  # Exclude metadata
                "total_questions": self._total_questions(),
            }

    # =========================================================================
    # PRIVATE HELPERS
    # =========================================================================

    def _initialize_metadata(self) -> None:
        """Initialize cache metadata if not present."""
        if CACHE_METADATA_KEY not in self.cache:
            self.cache[CACHE_METADATA_KEY] = {
                "version": CACHE_VERSION,
                "created": datetime.now().isoformat(),
                "updated": datetime.now().isoformat(),
                "total_pools": 0,
                "total_questions": 0,
            }

    def _update_metadata(self) -> None:
        """Update cache metadata before saving."""
        if CACHE_METADATA_KEY not in self.cache:
            self._initialize_metadata()

        self.cache[CACHE_METADATA_KEY]["version"] = CACHE_VERSION
        self.cache[CACHE_METADATA_KEY]["updated"] = datetime.now().isoformat()
        self.cache[CACHE_METADATA_KEY]["total_pools"] = (
            len(self.cache) - 1
        )  # Exclude metadata
        self.cache[CACHE_METADATA_KEY]["total_questions"] = self._total_questions()

    def _total_questions(self) -> int:
        """Get the total number of questions in the cache."""
        total = 0
        for key, value in self.cache.items():
            if key != CACHE_METADATA_KEY and isinstance(value, list):
                total += len(value)
        return total

    def _deduplicate_questions(
        self, new_questions: List[Dict[str, Any]], existing_pool: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Deduplicate new questions against existing pool.

        Delegates similarity checking to question_similarity module.

        Args:
            new_questions: List of questions to deduplicate
            existing_pool: Existing pool of questions

        Returns:
            List of unique questions (not already in pool)
        """
        unique = []

        for q in new_questions:
            # Check if question is similar to any in the pool
            if is_similar_to_pool(q, existing_pool):
                logger.debug(
                    f"Skipping text-similar question: {q.get('question', '')[:40]}..."
                )
                continue

            unique.append(q)

        return unique
