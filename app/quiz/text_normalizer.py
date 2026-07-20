"""
Shared text normalization utilities.

Used by:
- question_grounding.py
- question_explanation.py

Responsible only for cleaning text fragments.
"""

import re


def normalize_supporting_fact(text: str) -> str:
    """
    Turn a raw note fragment into a short atomic supporting fact.
    """

    if not text:
        return ""

    cleaned = str(text).strip()

    # Fix camelCase:
    # VirtualMachines -> Virtual Machines
    cleaned = re.sub(r"([a-z])([A-Z])", r"\1 \2", cleaned)
    # Fix common merged words
    # infixed-size -> in fixed-size
    # dataaccess -> data access
    # anapplication -> an application
    cleaned = re.sub(r"(?i)\b(in)(fixed)", r"\1 \2", cleaned)
    cleaned = re.sub(r"(?i)\b(data)(access)", r"\1 \2", cleaned)
    cleaned = re.sub(r"(?i)\b(an)(application)", r"\1 \2", cleaned)
    cleaned = re.sub(r"(?i)\b(remote)(servers)", r"\1 \2", cleaned)

    # Fix common merged words:
    # traditionalfiles -> traditional files
    # computingenvironments -> computing environments
    cleaned = re.sub(r"(?i)(traditional)(files)", r"\1 \2", cleaned)

    cleaned = re.sub(r"(?i)(computing)(environments)", r"\1 \2", cleaned)

    # Remove markdown headings
    cleaned = re.sub(r"^\s*#+\s*", "", cleaned)

    # Remove markdown bullets
    cleaned = re.sub(r"^\s*[-*+]\s*", "", cleaned)

    # Remove numbered lists
    cleaned = re.sub(r"^\s*\d+\.\s*", "", cleaned)

    # Convert Obsidian links:
    # [[Cloud Storage]] -> Cloud Storage
    cleaned = re.sub(r"\[\[(.*?)\]\]", r"\1", cleaned)

    # Remove markdown symbols
    cleaned = re.sub(r"[*_`>#]", "", cleaned)

    # Normalize spaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Remove trailing punctuation
    cleaned = cleaned.rstrip(" .")

    if not cleaned:
        return ""

    # Reject leftover markdown/web artifacts
    if any(
        marker in cleaned.lower()
        for marker in ["#", "[[", "]]", "---", "http", "https"]
    ):
        return ""

    # Do not truncate here.
    # Explanation and grounding require the full supporting fact.

    # Reject non-facts
    if cleaned.lower().startswith(
        (
            "how ",
            "why ",
            "what ",
            "when ",
            "where ",
            "conclusion",
            "summary",
            "overview",
            "references",
        )
    ):
        return ""

    return cleaned
