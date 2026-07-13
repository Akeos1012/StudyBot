"""
Grounding Processor Module - Prepares extracted facts for downstream quiz generation.

This module is responsible ONLY for validating, normalizing, and grounding
extracted facts before they enter the quiz generation pipeline.

Responsibilities:
- Validate facts against fact_schema.py
- Remove weak or invalid concepts
- Ensure every fact has required metadata (supporting_fact, source_note, fact_id)
- Deduplicate semantically identical facts
- Reject facts without supporting evidence

This module does NOT:
- Generate questions, explanations, or distractors
- Perform caching
- Score questions
- Build quizzes

The output is a clean, validated list of grounded facts ready for quiz generation.
"""

import hashlib
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict

from ..models.fact_schema import (
    validate_fact,
    normalize_fact,
    is_weak_concept,
    create_fact,
    ConceptType
)

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS
# ============================================================================

# Minimum fact quality score
MIN_FACT_SCORE = 5

# Maximum length for supporting fact
MAX_SUPPORTING_FACT_LENGTH = 220

# Minimum words in a supporting fact
MIN_SUPPORTING_FACT_WORDS = 4

# Maximum words in a supporting fact
MAX_SUPPORTING_FACT_WORDS = 24

# Default fact weight
DEFAULT_FACT_WEIGHT = 7

# File extension for notes
NOTE_EXTENSION = ".md"

# Patterns to reject in fact text
REJECTED_PATTERNS = [
    r'^\s*#+\s*',  # Markdown headers
    r'^\s*[-*+]\s*',  # Markdown bullets
    r'^\s*\d+\.\s*',  # Numbered lists
    r'\[\[(.*?)\]\]',  # Wiki links (preserve text)
    r'^\s*(how|why|what|when|where)\s',  # Question words at start
    r'\b(conclusion|summary|overview|references)\b',  # Section words
]

# Words that indicate weak concepts
WEAK_INDICATORS = {
    "example", "examples", "technique", "techniques",
    "approach", "approaches", "method", "methods",
    "process", "processes", "concept", "concepts",
    "system", "systems", "layer", "layers",
    "overview", "summary", "introduction", "conclusion",
    "types", "categories", "classification"
}

# ============================================================================
# EXCEPTIONS
# ============================================================================

class GroundingError(Exception):
    """Base exception for grounding errors."""
    pass


class FactValidationError(GroundingError):
    """Raised when a fact fails validation."""
    pass


class NoValidFactsError(GroundingError):
    """Raised when no valid facts are found."""
    pass


# ============================================================================
# MAIN CLASS
# ============================================================================

class GroundingProcessor:
    """
    Prepares extracted facts for downstream quiz generation.

    This class validates, normalizes, and grounds facts extracted from notes.
    It ensures all facts meet quality standards and have required metadata.

    Usage:
        processor = GroundingProcessor()
        grounded_facts = processor.ground_all(extracted_facts)
        if grounded_facts:
            # Use grounded_facts for quiz generation
    """

    def __init__(self, min_score: int = MIN_FACT_SCORE,
                 max_length: int = MAX_SUPPORTING_FACT_LENGTH):
        """
        Initialize the grounding processor.

        Args:
            min_score: Minimum quality score for a fact to be accepted
            max_length: Maximum length for supporting fact text
        """
        self.min_score = min_score
        self.max_length = max_length

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def ground_all(self, facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process and ground all facts.

        This is the main entry point for grounding extracted facts.

        Args:
            facts: List of extracted fact dictionaries

        Returns:
            List of validated, normalized, grounded facts

        Raises:
            NoValidFactsError: If no valid facts remain after grounding
        """
        if not facts:
            logger.warning("No facts provided to grounding processor")
            return []

        grounded = []

        for fact in facts:
            grounded_fact = self.ground_fact(fact)
            if grounded_fact:
                grounded.append(grounded_fact)

        if not grounded:
            logger.warning("No valid facts after grounding")
            return []

        # Deduplicate semantically identical facts
        deduplicated = self._deduplicate_facts(grounded)

        logger.info(f"Grounded {len(deduplicated)} facts from {len(facts)} input facts")
        return deduplicated

    def ground_fact(self, fact: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process and ground a single fact.

        Steps:
        1. Validate the fact using fact_schema.py
        2. Normalize the fact
        3. Validate the concept is not weak
        4. Clean supporting evidence
        5. Attach required metadata
        6. Score the fact for quality

        Args:
            fact: Extracted fact dictionary

        Returns:
            Grounded fact, or None if validation fails

        Raises:
            FactValidationError: If the fact fails validation (optional)
        """
        if not fact:
            return None

        # Step 1: Validate using fact_schema.py
        if not self._validate_fact_schema(fact):
            return None

        # Step 2: Normalize using fact_schema.py
        normalized = self._normalize_fact(fact)
        if not normalized:
            return None

        # Step 3: Check for weak concepts
        if self._is_weak_concept(normalized.get("concept", "")):
            logger.debug(f"Skipping weak concept: {normalized.get('concept')}")
            return None

        # Step 4: Clean supporting evidence
        evidence = self._clean_evidence(normalized)
        if not evidence:
            logger.debug(f"Fact has no supporting evidence: {normalized.get('concept')}")
            return None

        # Step 5: Build grounded fact with metadata
        grounded = self._build_grounded_fact(
            concept=normalized.get("concept", ""),
            definition=normalized.get("definition", ""),
            topic=normalized.get("topic", "Unknown"),
            source=normalized.get("source", "inline"),
            evidence=evidence,
            concept_type=normalized.get("concept_type", "concept")
        )

        # Step 6: Score the fact
        if not self._score_fact(grounded):
            logger.debug(f"Fact failed quality score: {grounded.get('concept')}")
            return None

        return grounded

    def validate_grounding(self, fact: Dict[str, Any]) -> bool:
        """
        Validate that a fact is properly grounded.

        Checks:
        - Has concept
        - Has definition/supporting fact
        - Has source_note
        - Has fact_id
        - Supporting fact is not empty

        Args:
            fact: The fact to validate

        Returns:
            True if properly grounded, False otherwise
        """
        if not fact:
            return False

        required = ["concept", "supporting_fact", "source_note", "fact_id"]
        missing = [f for f in required if f not in fact or not fact[f]]

        if missing:
            logger.debug(f"Fact missing required fields: {missing}")
            return False

        concept = fact.get("concept", "").strip()
        supporting = fact.get("supporting_fact", "").strip()

        if not concept or len(concept) < 2:
            logger.debug("Fact missing valid concept")
            return False

        if not supporting or len(supporting.split()) < MIN_SUPPORTING_FACT_WORDS:
            logger.debug("Fact missing supporting evidence")
            return False

        return True

    # =========================================================================
    # PRIVATE HELPERS - VALIDATION
    # =========================================================================

    def _validate_fact_schema(self, fact: Dict[str, Any]) -> bool:
        """Validate fact against fact_schema.py."""
        try:
            return validate_fact(fact)
        except Exception as e:
            logger.debug(f"Schema validation failed: {e}")
            return False

    def _normalize_fact(self, fact: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize fact using fact_schema.py."""
        try:
            return normalize_fact(fact)
        except Exception as e:
            logger.debug(f"Fact normalization failed: {e}")
            return None

    def _is_weak_concept(self, concept: str) -> bool:
        """Check if concept is weak using fact_schema.py."""
        if not concept:
            return True

        concept_lower = concept.lower()

        # Use fact_schema's is_weak_concept
        if is_weak_concept(concept_lower):
            return True

        # Additional checks
        if concept_lower in WEAK_INDICATORS:
            return True

        # Reject single-word generic concepts
        words = concept.split()
        if len(words) == 1 and len(concept) < 3:
            return True

        return False

    def _score_fact(self, fact: Dict[str, Any]) -> bool:
        """
        Score a fact for quality.

        Returns:
            True if score meets minimum threshold, False otherwise
        """
        score = self._compute_fact_score(fact)
        return score >= self.min_score

    def _compute_fact_score(self, fact: Dict[str, Any]) -> int:
        """
        Compute quality score for a fact.

        Scoring criteria:
        - Concept length (0-2)
        - Number of words in concept (0-2)
        - Capitalization (0-1)
        - Supporting fact word count (0-3)
        - Source weight (0-3)
        - Sentence clarity (0-1)
        """
        score = 0
        concept = fact.get("concept", "")
        supporting = fact.get("supporting_fact", "")

        # Concept quality
        if len(concept) > 3:
            score += 2
        if len(concept.split()) <= 3:
            score += 2
        if concept and concept[0].isupper():
            score += 1

        # Supporting fact quality
        word_count = len(supporting.split())
        if word_count >= 8:
            score += 3
        elif word_count >= 5:
            score += 1

        # Source weight
        if fact.get("is_header", False):
            score += 3
        elif fact.get("is_bullet", False):
            score += 1

        # Sentence clarity
        if supporting and supporting.strip().endswith('.'):
            score += 1

        # Penalize weak patterns
        concept_lower = concept.lower()
        if concept_lower in ['concept', 'example', 'type', 'method']:
            score -= 5
        if 'layer' in concept_lower:
            score -= 3

        # Bonus for strong concept types
        concept_type = fact.get("concept_type", "concept")
        if concept_type in ['algorithm', 'model', 'data_structure']:
            score += 2

        return max(0, score)

    # =========================================================================
    # PRIVATE HELPERS - CLEANING
    # =========================================================================

    def _clean_evidence(self, fact: Dict[str, Any]) -> Optional[str]:
        """
        Clean and validate supporting evidence.

        Args:
            fact: The fact dictionary

        Returns:
            Cleaned evidence text, or None if invalid
        """
        # Get evidence from various possible fields
        evidence = (
            fact.get("supporting_fact") or
            fact.get("sentence") or
            fact.get("definition") or
            fact.get("text") or
            ""
        )

        if not evidence:
            return None

        # Clean the text
        cleaned = self._clean_text(evidence)

        # Check minimum word count
        if len(cleaned.split()) < MIN_SUPPORTING_FACT_WORDS:
            return None

        # Check maximum word count
        if len(cleaned.split()) > MAX_SUPPORTING_FACT_WORDS:
            cleaned = ' '.join(cleaned.split()[:MAX_SUPPORTING_FACT_WORDS]).rstrip(' .')

        return cleaned

    def _clean_text(self, text: str) -> str:
        """
        Clean text by removing markdown and special characters.

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        cleaned = str(text).strip()

        # Remove markdown patterns
        for pattern in REJECTED_PATTERNS:
            cleaned = re.sub(pattern, '', cleaned)

        # Remove markdown formatting
        cleaned = re.sub(r'[*_`>#]', '', cleaned)

        # Normalize whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        # Remove trailing punctuation
        cleaned = cleaned.rstrip(' .')

        return cleaned

    # =========================================================================
    # PRIVATE HELPERS - BUILDING
    # =========================================================================

    def _build_grounded_fact(self, concept: str, definition: str,
                             topic: str, source: str,
                             evidence: str,
                             concept_type: str = "concept") -> Dict[str, Any]:
        """
        Build a fully grounded fact with metadata.

        Args:
            concept: The concept name
            definition: The definition text
            topic: The topic name
            source: The source path
            evidence: The cleaned supporting evidence
            concept_type: The concept type

        Returns:
            Complete grounded fact dictionary
        """
        # Get source note name
        source_note = self._extract_source_note(source)

        # Generate fact ID
        fact_id = self._generate_fact_id(topic, source_note, concept)

        # Build the fact
        grounded = create_fact(
            concept=concept,
            definition=definition or evidence,
            topic=topic,
            source=source,
            concept_type=concept_type
        )

        # Add grounding metadata
        grounded["supporting_fact"] = evidence
        grounded["source_note"] = source_note
        grounded["fact_id"] = fact_id
        grounded["weight"] = DEFAULT_FACT_WEIGHT
        grounded["answer"] = concept

        return grounded

    def _extract_source_note(self, source: str) -> str:
        """
        Extract source note name from source path.

        Args:
            source: Source path or string

        Returns:
            Source note name
        """
        if not source or source == "inline":
            return "inline"

        source_path = Path(str(source))
        return source_path.stem  # Filename without extension

    def _generate_fact_id(self, topic: str, source_note: str,
                          concept: str) -> str:
        """
        Generate a unique fact ID.

        Args:
            topic: The topic name
            source_note: The source note name
            concept: The concept name

        Returns:
            Unique fact ID
        """
        # Clean strings for ID
        topic_clean = self._slugify(topic)
        source_clean = self._slugify(source_note)
        concept_clean = self._slugify(concept)[:20]

        return f"{topic_clean}_{source_clean}_{concept_clean}"

    def _slugify(self, text: str) -> str:
        """
        Convert text to a URL-friendly slug.

        Args:
            text: The text to slugify

        Returns:
            Slugified text
        """
        if not text:
            return "unknown"

        # Convert to lowercase, replace non-alphanumeric with underscore
        slug = re.sub(r'[^a-z0-9]+', '_', str(text).lower()).strip('_')
        return slug or "unknown"

    # =========================================================================
    # PRIVATE HELPERS - DEDUPLICATION
    # =========================================================================

    def _deduplicate_facts(self, facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deduplicate semantically identical facts.

        Args:
            facts: List of grounded facts

        Returns:
            Deduplicated list of facts
        """
        seen_concepts = set()
        unique = []

        for fact in facts:
            concept = fact.get("concept", "").lower()

            # Skip if we've seen this concept
            if concept in seen_concepts:
                continue

            # Check semantic similarity with existing facts
            is_duplicate = False
            supporting = fact.get("supporting_fact", "").lower()

            for existing in unique:
                existing_supporting = existing.get("supporting_fact", "").lower()

                # Check if supporting facts are too similar
                if self._is_semantically_similar(supporting, existing_supporting):
                    is_duplicate = True
                    break

            if not is_duplicate:
                seen_concepts.add(concept)
                unique.append(fact)

        return unique

    def _is_semantically_similar(self, text1: str, text2: str,
                                  threshold: float = 0.7) -> bool:
        """
        Check if two texts are semantically similar.

        Uses word overlap as a simple similarity measure.

        Args:
            text1: First text
            text2: Second text
            threshold: Similarity threshold

        Returns:
            True if texts are similar, False otherwise
        """
        if not text1 or not text2:
            return False

        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return False

        overlap = len(words1 & words2)
        union = len(words1 | words2)

        return (overlap / union) > threshold