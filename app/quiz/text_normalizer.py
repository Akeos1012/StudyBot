"""
Shared text normalization utilities.

Used by:
- question_grounding.py
- question_explanation.py

Responsible only for cleaning text fragments.
"""

import re


def normalize_supporting_fact(text: str) -> str:

    text = (
        text
        .replace("â€“", "-")
        .replace("â€”", "-")
        .replace("â€™", "'")
        .replace("â€œ", '"')
        .replace("â€", '"')
        .replace("â", "")
    )

    """
    Turn a raw note fragment into a short atomic supporting fact.
    """

    if not text:
        return ""

    cleaned = str(text).strip()

    # Remove remaining encoding artifacts
    cleaned = re.sub(
        r"[\x80-\x9F]",
        "",
        cleaned
    )

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

    # Fix common accidental word joins from extraction
    merged_words = {
        "pieceofdata": "piece of data",
        "computingand": "computing and",
        "systemswhere": "systems where",
        "handledby": "handled by",
        "accessedthrough": "accessed through",
        "storedon": "stored on",
        "usingcloud": "using cloud",
        "usersand": "users and",
        "applicationsand": "applications and",
        "independentpiece": "independent piece",
        "managementof": "management of",
    }

    for bad, good in merged_words.items():
        cleaned = re.sub(
            rf"(?i)\b{bad}\b",
            good,
            cleaned
        )

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

    # Remove repeated concept definition starters
    cleaned = re.sub(
        r"^(a|an)\s+[a-z]+(?:\s+[a-z]+)?\s+(refers to|is|are|means)\s+",
        "",
        cleaned,
        flags=re.IGNORECASE
    )

    # Remove trailing punctuation
    cleaned = cleaned.rstrip(" .,;:")

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
