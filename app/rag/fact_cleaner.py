# =====================================================
# PIPELINE CHECKPOINT: FACT NORMALIZATION LAYER
#
# Position:
#
# Raw Extracted Fact
#        ↓
# FactCleaner
#        ↓
# Clean Fact Object
#        ↓
# FactCache
#        ↓
# Quiz Generation
#
# Purpose:
# Normalizes extracted facts before persistent storage.
#
# Responsibilities:
# - Fix encoding corruption
# - Remove markdown artifacts
# - Normalize whitespace
# - Clean concept formatting
# - Remove duplicate concept prefixes
#
# Connected Modules:
#
# Receives from:
#   - app/rag/fact_extractor.py
#
# Used by:
#   - app/rag/fact_cache.py
#
# Output:
#   - Clean fact dictionary
#
# IMPORTANT RULES:
#
# - Never add new knowledge.
# - Never rewrite meaning.
# - Never summarize definitions.
# - Only normalize formatting.
#
# Risk:
# Aggressive cleaning can damage factual meaning.
#
# =====================================================
import re
from typing import Dict, Any, List

# ============================================================================
# CONSTANTS
# ============================================================================

# Common encoding corruption fixes
ENCODING_FIXES = {
    "â€“": "-",
    "â€”": "-",
    "â€œ": '"',
    "â€": '"',
    "â€™": "'",
    "â€¦": "...",
}

# Patterns to remove from text
MARKDOWN_PATTERNS = [
    r"[*_#`]",  # Markdown formatting
    r"(?m)^\s*[-*+]\s+",
]

# Patterns to normalize
WHITESPACE_PATTERN = r"\s+"
CAMEL_CASE_PATTERN = r"([a-z])([A-Z])"

# ============================================================================
# PUBLIC FUNCTIONS
# ============================================================================

"""
    FUNCTION CHECKPOINT:
    TEXT NORMALIZATION

    Stage:

        Raw Text
            ↓
        Clean Text

    Handles:
        - Encoding repair
        - Markdown removal
        - Whitespace normalization
        - Word boundary fixes

    Input:
        Raw extracted text

    Output:
        Normalized text

    Must preserve:
        - Meaning
        - Technical terms
        - Sentence information

    Must not:
        - Remove factual content
        - Add explanations
        - Change terminology
"""

def clean_text(text: str) -> str:
    """
    Clean general text formatting.

    Args:
        text: Raw text string

    Returns:
        Cleaned text string
    """
    if not text:
        return ""

    # Fix encoding corruption
    for bad, good in ENCODING_FIXES.items():
        text = text.replace(bad, good)

    # Remove markdown formatting
    for pattern in MARKDOWN_PATTERNS:
        text = re.sub(pattern, "", text)

    # Remove HTML tags like <u>, </u>, <b>, <i>
    text = re.sub(r"<[^>]+>", "", text)

    # Normalize whitespace
    text = re.sub(WHITESPACE_PATTERN, " ", text)

    # Add spaces between camelCase words only
    # Example: cloudStorage -> cloud Storage
    # Avoid splitting normal words like "data", "information"
    text = re.sub(
        r"([a-z]{2,})([A-Z][a-z]+)",
        r"\1 \2",
        text
    )

    # Fix common missing word boundaries
    WORD_BOUNDARY_FIXES = {
        "tothe": "to the",
        "inthe": "in the",
        "fromthe": "from the",
        "ofthe": "of the",
        "onthe": "on the",
        "forthe": "for the",

        "relyingon": "relying on",
        "accessand": "access and",
        "accessedthrough": "accessed through",
        "usecomputing": "use computing",
        "resourceson": "resources on",

        "theservice": "the service",
        "dataremotely": "data remotely",
        "computingand": "computing and",
        "devicessuch": "devices such",
        "fileson": "files on",
        "storedon": "stored on",
        "infrastructureover": "infrastructure over",
        "internetinstead": "internet instead",
    }

    # Add spaces only for real camelCase words
    text = re.sub(
        r"([a-z])([A-Z][a-z]+)",
        r"\1 \2",
        text
    )

    # Normalize whitespace after all replacements
    text = re.sub(r"\s+", " ", text)

    for bad, good in WORD_BOUNDARY_FIXES.items():
        text = re.sub(
            bad,
            good,
            text,
            flags=re.IGNORECASE
        )

    # Fix remaining missing spaces between joined words
    text = re.sub(
        r"([a-z])([A-Z])",
        r"\1 \2",
        text
    )

    # Normalize whitespace again after replacements
    text = re.sub(r"\s+", " ", text)

    return text.strip()

"""
    FUNCTION CHECKPOINT:
    CONCEPT NORMALIZATION

    Stage:

        Extracted Concept
              ↓
        Canonical Concept Name

    Handles:
        - Formatting cleanup
        - Separator removal
        - Text normalization

    Used before:
        Fact storage

    Must preserve:
        - Concept identity
        - Acronyms
        - Technical naming

    Must not:
        - Rename concepts
        - Classify concepts
        - Validate concepts
"""

def clean_concept(concept: str) -> str:

    if not concept:
        return ""

    concept = clean_text(concept)

    # Remove trailing separators (colon, dash, em dash, en dash)
    concept = re.sub(r"[-:–—]+$", "", concept)

    return concept.strip()

"""
    FUNCTION CHECKPOINT:
    DEFINITION NORMALIZATION

    Stage:

        Raw Definition
              ↓
        Clean Definition

    Handles:
        - Duplicate concept removal
        - Formatting cleanup

    Input:
        Concept + extracted definition

    Output:
        Clean definition text

    Must preserve:
        - Original explanation
        - Supporting information

    Must not:
        - Shorten meaning
        - Generate missing information
        - Rewrite explanation
"""

def clean_definition(concept: str, definition: str) -> str:
    """
    Clean fact definition.

    Preserves the concept name in the definition to ensure grounding validation works,
    while removing any redundant prefix repetition.
    """

    if not definition:
        return ""

    definition = clean_text(definition)

    if not concept:
        return definition

    # Remove repeated concept at sentence start, if it is clearly duplicated
    # (e.g., "Deep Learning: Deep Learning is..." -> "Deep Learning is...")
    duplicate_pattern = (
        rf"^{re.escape(concept)}\s*[-:–—]?\s*"
        rf"{re.escape(concept)}\b\s*"
    )

    definition = re.sub(
        duplicate_pattern,
        f"{concept} ",
        definition,
        flags=re.IGNORECASE
    )

    return definition.strip()


"""
    FUNCTION CHECKPOINT:
    FACT FINALIZATION

    Stage:

        Extracted Fact
              ↓
        Normalized Fact
              ↓
        FactCache

    Input:
        Raw fact dictionary

    Output:
        Cache-ready fact dictionary

    Cleans:
        - Concept
        - Definition
        - Supporting fact

    Connected:

        FactExtractor
              ↓
        FactCleaner
              ↓
        FactCache

    Must preserve:
        - Fact ID
        - Topic
        - Source
        - Concept meaning

    Must not:
        - Create facts
        - Reject knowledge
        - Modify truth
"""

def clean_fact(fact: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean a complete fact dictionary.

    Args:
        fact: Raw fact dictionary with 'concept', 'definition', and optional 'sentence'

    Returns:
        Cleaned fact dictionary
    """
    if not fact:
        return {}

    cleaned = fact.copy()

    # Clean concept
    concept = clean_concept(cleaned.get("concept", ""))

    # Clean definition using the cleaned concept
    definition = clean_definition(concept, cleaned.get("definition", ""))

    cleaned["concept"] = concept
    cleaned["definition"] = definition

    # Keep sentence identical to cleaned definition
    cleaned["sentence"] = definition

    if "supporting_fact" in cleaned:
        cleaned["supporting_fact"] = clean_definition(
            concept,
            cleaned["supporting_fact"]
        )

    return cleaned


def clean_facts(facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Clean multiple facts.

    Args:
        facts: List of raw fact dictionaries

    Returns:
        List of cleaned fact dictionaries
    """
    if not facts:
        return []

    return [clean_fact(fact) for fact in facts if fact]


# ============================================================================
# MODULE TEST
# ============================================================================

if __name__ == "__main__":
    # Test the cleaner
    test_fact = {
        "concept": "Cloud Storage:",
        "definition": "Cloud Storage: Cloud Storage allows users to store files remotely.",
        "sentence": "Cloud Storage is a service.",
    }

    print("Original:", test_fact)
    print("Cleaned:", clean_fact(test_fact))
