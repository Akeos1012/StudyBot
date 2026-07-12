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


ENCODING_FIXES = {
    "â€“": "-",
    "â€”": "-",
    "â€œ": '"',
    "â€": '"',
    "â€™": "'",
    "â€¦": "...",
}


def clean_text(text: str) -> str:
    """
    Clean general text formatting.
    """

    if not text:
        return ""

    for bad, good in ENCODING_FIXES.items():
        text = text.replace(bad, good)

    # Remove markdown formatting
    text = re.sub(r"[*_#`]", "", text)

    # Normalize spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def clean_concept(concept: str) -> str:
    """
    Clean concept names.
    """

    concept = clean_text(concept)

    # Remove trailing separators
    concept = re.sub(r"[-:–—]+$", "", concept)

    return concept.strip()


def clean_definition(concept: str, definition: str) -> str:
    """
    Clean fact definition.
    """

    definition = clean_text(definition)

    if not definition:
        return ""

    # Remove duplicated concept prefix
    pattern = rf"^{re.escape(concept)}\s*[-:]\s*"

    definition = re.sub(
        pattern,
        "",
        definition,
        flags=re.IGNORECASE
    )

    return definition.strip()


def clean_fact(fact: dict) -> dict:
    """
    Clean a complete fact dictionary.
    """

    cleaned = fact.copy()

    concept = clean_concept(
        cleaned.get("concept", "")
    )

    definition = clean_definition(
        concept,
        cleaned.get("definition", "")
    )

    cleaned["concept"] = concept
    cleaned["definition"] = definition

    if "sentence" in cleaned:
        cleaned["sentence"] = clean_text(
            cleaned["sentence"]
        )

    return cleaned


def clean_facts(facts: list) -> list:
    """
    Clean multiple facts.
    """

    return [
        clean_fact(fact)
        for fact in facts
        if fact
    ]