"""
Fact Cleaner Module

Responsible for cleaning extracted facts before saving them into cache.

Handles:
- Encoding corruption
- Markdown artifacts
- Duplicate concept names inside definitions
- Whitespace cleanup
- Basic normalization
"""

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
    r"^-\s*",  # Markdown list bullets (start of line)
    r"^\\-\s*",  # Escaped list bullets
]

# Patterns to normalize
WHITESPACE_PATTERN = r"\s+"
CAMEL_CASE_PATTERN = r"([a-z])([A-Z])"

# ============================================================================
# PUBLIC FUNCTIONS
# ============================================================================


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

    # Normalize whitespace
    text = re.sub(WHITESPACE_PATTERN, " ", text)

    # Add spaces between camelCase words (e.g., "cloudStorage" -> "cloud Storage")
    text = re.sub(CAMEL_CASE_PATTERN, r"\1 \2", text)

        # Fix common missing word boundaries
    WORD_BOUNDARY_FIXES = {
        "serverswithout": "servers without",
        "remoteservers": "remote servers",
        "accessedover": "accessed over",
        "savingfiles": "saving files",
        "cloudstorage": "cloud storage",
    }

    for bad, good in WORD_BOUNDARY_FIXES.items():
        text = text.replace(bad, good)

    return text.strip()


def clean_concept(concept: str) -> str:
    """
    Clean concept names.

    Args:
        concept: Raw concept string

    Returns:
        Cleaned concept string
    """
    if not concept:
        return ""

    concept = clean_text(concept)

    # Remove trailing separators (colon, dash, em dash, en dash)
    concept = re.sub(r"[-:–—]+$", "", concept)

    return concept.strip()


def clean_definition(concept: str, definition: str) -> str:
    """
    Clean fact definition.

    Removes duplicated concept names inside definitions.
    """

    if not definition:
        return ""

    definition = clean_text(definition)

    if not concept:
        return definition

    # Remove concept prefix
    pattern = rf"^{re.escape(concept)}\s*[-:–—]?\s*"
    definition = re.sub(
        pattern,
        "",
        definition,
        flags=re.IGNORECASE
    )

    # Remove repeated concept at sentence start
    duplicate_pattern = (
        rf"\b{re.escape(concept)}\b\s+"
        rf"\b{re.escape(concept)}\b"
    )

    definition = re.sub(
        duplicate_pattern,
        concept,
        definition,
        flags=re.IGNORECASE
    )

    return definition.strip()


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

    # Clean optional fields
    if "sentence" in cleaned:
        cleaned["sentence"] = clean_text(cleaned["sentence"])

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
