"""
Shared fact schema for the AI Study Companion.
All facts must follow this structure.

This module provides:
- Concept types and type compatibility
- Fact validation and normalization
- Fact creation and type detection
- Question type recommendations
- Fact object with type-aware comparison
- Statistics and data cleaning helpers
"""

from typing import Dict, Any, Optional, List, Set
from enum import Enum
import re
from collections import Counter

# ============================================================================
# ENUMS
# ============================================================================


class ConceptType(Enum):
    """Semantic types for concepts to prevent invalid comparisons."""

    ALGORITHM = "algorithm"
    MODEL = "model"
    METRIC = "metric"
    SYSTEM = "system"
    PROCESS = "process"
    CONCEPT = "concept"
    DATA_STRUCTURE = "data_structure"
    FRAMEWORK = "framework"
    LANGUAGE = "language"
    PARADIGM = "paradigm"
    APPLICATION = "application"

    @classmethod
    def get_compatible_types(cls, type_name: str) -> List[str]:
        """Get types that can be meaningfully compared with this type."""
        return _COMPATIBILITY_MAP.get(type_name, [type_name])

    @classmethod
    def can_compare(cls, type_a: str, type_b: str) -> bool:
        """Check if two concept types can be meaningfully compared."""
        if type_a == type_b:
            return True
        compatible_a = cls.get_compatible_types(type_a)
        compatible_b = cls.get_compatible_types(type_b)
        return type_b in compatible_a or type_a in compatible_b

    @classmethod
    def get_hierarchy(cls) -> Dict[str, Dict[str, Any]]:
        """Get the type hierarchy."""
        return _TYPE_HIERARCHY


# ============================================================================
# CONSTANTS
# ============================================================================

# ===== Required and Optional Schema Keys =====
REQUIRED_KEYS = ["concept", "definition", "topic", "source"]
OPTIONAL_KEYS = [
    "difficulty_hint",
    "weight",
    "is_header",
    "is_bullet",
    "sentence",
    "concept_type",
]
DIFFICULTY_HINTS = ["easy", "medium", "hard"]

# ===== Weak Concepts (for filtering) =====
WEAK_CONCEPTS = {
    "example",
    "examples",
    "technique",
    "techniques",
    "approach",
    "approaches",
    "method",
    "methods",
    "process",
    "processes",
    "concept",
    "concepts",
    "system",
    "systems",
    "layer",
    "layers",
    "overview",
    "summary",
    "introduction",
    "conclusion",
    "types",
    "categories",
    "classification",
}

# ===== Hard Rejections =====
HARD_INVALID_CONCEPTS = {
    "Examples",
    "Overview",
    "Summary",
    "Notes",
    "Definition",
    "Introduction",
    "Conclusion",
    "References",
    "Table of Contents",
    "Index",
    "Glossary",
    "Bibliography",
    "Acknowledgements",
}

# ===== Soft Warnings =====
SOFT_WARNING_CONCEPTS = {
    "Concept",
    "Example",
    "Method",
    "Technique",
    "Approach",
    "Process",
    "System",
    "Layer",
    "Types",
    "Categories",
    "Classification",
    "Techniques",
    "Methods",
    "Approaches",
    "Processes",
    "Pattern",
    "Model",
    "Framework",
    "Architecture",
}

# ===== Invalid Patterns (regex) =====
INVALID_CONCEPT_PATTERNS = [
    r"^types?\s+of",
    r"^why\s",
    r"^how\s",
    r".*layer$",
    r".*&.*layer",
    r"^simple analogy",
    r"^performance",
    r"^overview",
    r"^summary",
    r"^introduction",
    r"^conclusion",
    r"^references",
    r"^examples?$",
    r"^technique examples?$",
    r"^notes$",
    r"^definition$",
]

# ===== Concept Type Keywords =====
CONCEPT_TYPE_KEYWORDS = {
    ConceptType.ALGORITHM: [
        "sort",
        "search",
        "algorithm",
        "traversal",
        "recursion",
        "divide and conquer",
        "dynamic programming",
        "greedy",
        "backtracking",
        "branch and bound",
    ],
    ConceptType.MODEL: [
        "network",
        "neural",
        "model",
        "regression",
        "classification",
        "clustering",
        "deep learning",
        "machine learning",
        "cnn",
        "rnn",
        "transformer",
        "bert",
        "gpt",
    ],
    ConceptType.METRIC: [
        "complexity",
        "time",
        "space",
        "accuracy",
        "precision",
        "recall",
        "f1",
        "performance",
        "efficiency",
        "big o",
        "memory",
        "speed",
        "throughput",
        "latency",
    ],
    ConceptType.DATA_STRUCTURE: [
        "array",
        "list",
        "tree",
        "graph",
        "hash",
        "map",
        "set",
        "queue",
        "stack",
        "heap",
        "trie",
        "linked list",
    ],
    ConceptType.SYSTEM: [
        "system",
        "architecture",
        "infrastructure",
        "platform",
        "database",
        "storage",
        "server",
        "client",
        "api",
    ],
    ConceptType.PROCESS: [
        "process",
        "pipeline",
        "workflow",
        "lifecycle",
        "development",
        "deployment",
        "integration",
        "testing",
        "monitoring",
    ],
    ConceptType.FRAMEWORK: [
        "framework",
        "library",
        "sdk",
        "toolkit",
        "platform",
        "tensorflow",
        "pytorch",
        "scikit",
        "django",
        "react",
    ],
    ConceptType.PARADIGM: [
        "paradigm",
        "functional",
        "object-oriented",
        "procedural",
        "declarative",
        "imperative",
        "symbolic",
        "connectionist",
    ],
    ConceptType.APPLICATION: [
        "vision",
        "nlp",
        "speech",
        "recognition",
        "recommendation",
        "generation",
        "translation",
        "summarization",
    ],
}

# ===== Type -> Question Type Mapping =====
_QUESTION_TYPE_MAP = {
    "algorithm": ["definition", "comparison", "application"],
    "model": ["definition", "application", "scenario"],
    "metric": ["definition", "comparison"],
    "process": ["definition", "scenario"],
    "concept": ["definition", "scenario"],
    "data_structure": ["definition", "application"],
    "framework": ["definition", "comparison"],
    "language": ["definition"],
    "paradigm": ["definition", "comparison"],
    "application": ["scenario", "application"],
}

# ===== Type -> Difficulty Map =====
_QUESTION_DIFFICULTY_MAP = {
    ("algorithm", "definition"): 0.3,
    ("algorithm", "comparison"): 0.6,
    ("algorithm", "application"): 0.7,
    ("model", "definition"): 0.4,
    ("model", "application"): 0.6,
    ("model", "scenario"): 0.8,
    ("metric", "definition"): 0.5,
    ("metric", "comparison"): 0.7,
    ("process", "definition"): 0.4,
    ("process", "scenario"): 0.7,
    ("concept", "definition"): 0.3,
    ("concept", "scenario"): 0.6,
}

# ===== Type Hierarchy =====
_TYPE_HIERARCHY = {
    "algorithm": {
        "parent": None,
        "children": ["sorting", "searching", "optimization", "dynamic_programming"],
        "level": 1,
    },
    "model": {
        "parent": None,
        "children": ["neural_network", "transformer", "regression", "classification"],
        "level": 1,
    },
    "metric": {
        "parent": None,
        "children": ["complexity", "performance", "accuracy"],
        "level": 1,
    },
    "process": {
        "parent": None,
        "children": ["training", "inference", "optimization"],
        "level": 1,
    },
    "concept": {
        "parent": None,
        "children": ["paradigm", "framework", "architecture"],
        "level": 1,
    },
    "data_structure": {
        "parent": "algorithm",
        "children": ["array", "tree", "graph", "hash"],
        "level": 2,
    },
    "framework": {
        "parent": "model",
        "children": ["tensorflow", "pytorch", "sklearn"],
        "level": 2,
    },
}

# ===== Compatibility Map =====
_COMPATIBILITY_MAP = {
    "algorithm": ["algorithm", "data_structure"],
    "model": ["model", "framework"],
    "metric": ["metric"],
    "system": ["system", "framework"],
    "process": ["process", "paradigm"],
    "concept": ["concept", "paradigm"],
    "data_structure": ["data_structure", "algorithm"],
    "framework": ["framework", "system", "model"],
    "language": ["language", "paradigm"],
    "paradigm": ["paradigm", "process", "concept"],
    "application": ["application", "system"],
}

# ============================================================================
# INTERNAL HELPERS
# ============================================================================


def _is_hard_invalid_concept(concept: str) -> bool:
    """Check if concept is in the hard reject list."""
    return concept in HARD_INVALID_CONCEPTS


def _matches_invalid_pattern(concept: str) -> bool:
    """Check if concept matches any invalid regex pattern."""
    concept_lower = concept.lower()
    for pattern in INVALID_CONCEPT_PATTERNS:
        if re.match(pattern, concept_lower):
            return True
    return False


def _has_duplicate_words(concept: str) -> bool:
    """Check if concept has duplicate words."""
    words = concept.split()
    return len(words) != len(set(words))


def _has_redundant_pattern(concept: str) -> bool:
    """
    Check if concept contains redundant word patterns.

    FIX: Only detects TRUE redundancy (words appearing multiple times),
    not legitimate multi-word concepts.
    """
    concept_lower = concept.lower()
    words = concept_lower.split()

    # Check if any word appears more than once (true redundancy)
    word_counts = {}
    for word in words:
        word_counts[word] = word_counts.get(word, 0) + 1

    # If any word appears more than once, it's redundant
    for count in word_counts.values():
        if count > 1:
            return True

    return False


def _is_soft_warning_concept(concept: str) -> bool:
    """Check if concept is in the soft warning list."""
    return concept in SOFT_WARNING_CONCEPTS


def _is_generic_layer(concept: str) -> bool:
    """Check if concept is a generic layer term."""
    concept_lower = concept.lower()
    return "layer" in concept_lower and len(concept_lower.split()) == 1


# ============================================================================
# VALIDATION RULES
# ============================================================================


def validate_concept_name(concept: str) -> bool:
    """
    Validate concept names with SOFT warnings instead of hard rejections.
    Only truly invalid concepts are hard rejected.
    """
    if not concept or len(concept) < 2:
        return False

    # HARD REJECT: Check exact invalid matches
    if _is_hard_invalid_concept(concept):
        return False

    # HARD REJECT: Check invalid patterns
    if _matches_invalid_pattern(concept):
        return False

    # HARD REJECT: Check for duplicate words
    if _has_duplicate_words(concept):
        return False

    # HARD REJECT: Check for redundant patterns
    if _has_redundant_pattern(concept):
        return False

    # SOFT WARNING: Log but don't reject
    if _is_soft_warning_concept(concept):
        print(f"⚠️ Soft warning: '{concept}' is a generic term - accepting anyway")

    # HARD REJECT: Check for generic layer
    if _is_generic_layer(concept):
        return False

    return True


def validate_fact(fact: Dict[str, Any]) -> bool:
    """Validate that a fact has the correct schema."""
    # Check required keys
    for key in REQUIRED_KEYS:
        if key not in fact:
            return False
        if not fact[key] or not str(fact[key]).strip():
            return False

    # Validate concept
    concept = str(fact["concept"]).strip()
    if not validate_concept_name(concept):
        return False

    # Validate definition
    definition = str(fact["definition"]).strip()
    if len(definition) < 5:
        return False

    # Validate concept_type if present
    if "concept_type" in fact and fact["concept_type"]:
        if not any(t.value == fact["concept_type"] for t in ConceptType):
            return False

    return True


# ============================================================================
# NORMALIZATION
# ============================================================================


def _extract_concept(fact: Dict[str, Any]) -> Optional[str]:
    """Extract concept from fact using multiple possible keys."""
    concept = (
        fact.get("concept")
        or fact.get("answer")
        or fact.get("statement")
        or fact.get("name")
        or fact.get("title")
    )
    return str(concept).strip() if concept else None


def _extract_definition(fact: Dict[str, Any]) -> Optional[str]:
    """Extract definition from fact using multiple possible keys."""
    definition = (
        fact.get("definition")
        or fact.get("sentence")
        or fact.get("description")
        or fact.get("content")
        or fact.get("text")
    )
    return str(definition).strip() if definition else None


def _normalize_concept_type(fact: Dict[str, Any], concept: str, definition: str) -> str:
    """Normalize the concept type field."""
    concept_type = fact.get("concept_type")
    if not concept_type:
        return detect_concept_type(concept, definition)
    if isinstance(concept_type, str):
        for ct in ConceptType:
            if ct.value == concept_type.lower():
                return ct.value
    return concept_type


def normalize_fact(fact: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Normalize a fact to ensure it has the correct schema."""
    if not fact:
        return None

    concept = _extract_concept(fact)
    definition = _extract_definition(fact)

    if not concept or not definition:
        return None

    # Validate concept
    if not validate_concept_name(concept):
        return None

    # Skip if definition is too short
    if len(definition) < 5:
        return None

    concept_type = _normalize_concept_type(fact, concept, definition)

    return {
        "concept": concept,
        "definition": definition,
        "topic": fact.get("topic", "Unknown"),
        "source": fact.get("source", "Unknown"),
        "sentence": fact.get("sentence", definition),
        "concept_type": concept_type,
        "difficulty_hint": fact.get("difficulty_hint", "medium"),
        "weight": fact.get("weight", 5),
        "is_header": fact.get("is_header", False),
        "is_bullet": fact.get("is_bullet", False),
    }


# ============================================================================
# FACT CREATION
# ============================================================================


def create_fact(
    concept: str,
    definition: str,
    topic: str = "Unknown",
    source: str = "Unknown",
    concept_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new fact with the correct schema."""
    if not validate_concept_name(concept):
        raise ValueError(f"Invalid concept name: {concept}")

    if not concept_type:
        concept_type = detect_concept_type(concept, definition)

    return {
        "concept": concept.strip(),
        "definition": definition.strip(),
        "topic": topic.strip(),
        "source": source.strip(),
        "sentence": definition.strip(),
        "concept_type": concept_type,
        "difficulty_hint": "medium",
        "weight": 5,
        "is_header": False,
        "is_bullet": False,
    }


# ============================================================================
# TYPE DETECTION
# ============================================================================


def detect_concept_type(concept: str, definition: str = "") -> str:
    """Auto-detect the concept type based on keywords."""
    text = f"{concept} {definition}".lower()

    type_scores = {}
    for concept_type, keywords in CONCEPT_TYPE_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > 0:
            type_scores[concept_type.value] = score

    if type_scores:
        return max(type_scores, key=type_scores.get)
    return "concept"


# ============================================================================
# WEAK CONCEPT DETECTION
# ============================================================================


def is_weak_concept(concept: str) -> bool:
    """Check if a concept is likely weak or invalid."""
    concept_lower = concept.lower()
    for pattern in WEAK_CONCEPTS:
        if pattern in concept_lower:
            return True
    return False


# ============================================================================
# TYPE COMPARISON HELPERS
# ============================================================================


def can_compare_concepts(type_a: str, type_b: str) -> bool:
    """Check if two concept types can be meaningfully compared."""
    return ConceptType.can_compare(type_a, type_b)


def get_compatible_types(type_name: str) -> List[str]:
    """Get list of compatible concept types."""
    return ConceptType.get_compatible_types(type_name)


def get_type_hierarchy() -> Dict[str, Dict[str, Any]]:
    """Get the full type hierarchy."""
    return ConceptType.get_hierarchy()


# ============================================================================
# QUESTION HELPERS
# ============================================================================


def get_question_types_for_type(concept_type: str) -> List[str]:
    """Get recommended question types for a concept type."""
    return _QUESTION_TYPE_MAP.get(concept_type, ["definition"])


def get_question_difficulty(concept_type: str, question_type: str) -> float:
    """Get difficulty score for a question type given a concept type."""
    return _QUESTION_DIFFICULTY_MAP.get((concept_type, question_type), 0.5)


# ============================================================================
# FACT CLASS
# ============================================================================


class Fact:
    """Fact object with type-aware comparison support."""

    def __init__(self, data: Dict[str, Any]):
        self.data = normalize_fact(data)
        if not self.data:
            raise ValueError("Invalid fact data")
        self.id = hash(f"{self.data['concept']}{self.data['topic']}")

    @property
    def concept(self) -> str:
        return self.data["concept"]

    @property
    def definition(self) -> str:
        return self.data["definition"]

    @property
    def topic(self) -> str:
        return self.data["topic"]

    @property
    def concept_type(self) -> str:
        return self.data.get("concept_type", "concept")

    @property
    def source(self) -> str:
        return self.data["source"]

    @property
    def difficulty_hint(self) -> str:
        return self.data.get("difficulty_hint", "medium")

    @property
    def weight(self) -> int:
        return self.data.get("weight", 5)

    def can_compare_with(self, other: "Fact") -> bool:
        """Check if this fact can be meaningfully compared with another."""
        return can_compare_concepts(self.concept_type, other.concept_type)

    def get_question_types(self) -> List[str]:
        """Get recommended question types for this fact."""
        return get_question_types_for_type(self.concept_type)

    def get_difficulty_for_question(self, question_type: str) -> float:
        """Get difficulty for a specific question type."""
        return get_question_difficulty(self.concept_type, question_type)

    def to_dict(self) -> Dict[str, Any]:
        return self.data.copy()

    def __repr__(self) -> str:
        return f"Fact(concept='{self.concept}', type='{self.concept_type}', topic='{self.topic}')"


# ============================================================================
# DATA CLEANING HELPERS
# ============================================================================


def _suggest_fix(concept: str) -> str:
    """Suggest a fix for a corrupted concept."""
    # Remove duplicate words
    words = concept.split()
    unique_words = []
    seen = set()
    for w in words:
        if w.lower() not in seen:
            unique_words.append(w)
            seen.add(w.lower())
    fixed = " ".join(unique_words)

    # Handle specific cases
    if "World Data Data Augmentation" in concept:
        fixed = "Data Augmentation"
    elif "Data Augmentation" in concept and len(concept.split()) > 3:
        fixed = "Data Augmentation"

    return fixed


def find_corrupted_concepts(facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Find concepts that are likely corrupted."""
    corrupted = []

    for f in facts:
        concept = f.get("concept", "")
        if not concept:
            continue

        issues = []

        # Check for duplicate words
        words = concept.split()
        if len(words) != len(set(words)):
            issues.append("duplicate_words")

        # Check for invalid patterns
        concept_lower = concept.lower()
        for pattern in INVALID_CONCEPT_PATTERNS:
            if re.match(pattern, concept_lower):
                issues.append("invalid_pattern")
                break

        if issues:
            corrupted.append(
                {
                    "concept": concept,
                    "issues": issues,
                    "suggestion": _suggest_fix(concept),
                }
            )

    return corrupted


# ============================================================================
# TYPE STATISTICS
# ============================================================================


def get_type_stats(facts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Get statistics about concept types in a fact list."""
    types = Counter(f.get("concept_type", "unknown") for f in facts)
    topics = Counter(f.get("topic", "unknown") for f in facts)

    return {
        "total_facts": len(facts),
        "type_distribution": dict(types),
        "topic_distribution": dict(topics),
        "unique_types": len(types),
        "most_common_type": types.most_common(1)[0][0] if types else None,
    }
