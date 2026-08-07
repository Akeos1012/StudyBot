"""
MODULE: Text Normalizer

LOCATION:
app/quiz/text_normalizer.py


PIPELINE POSITION:

Obsidian Note
      |
      v
FactExtractor
      |
      v
Raw Supporting Fact
      |
      v
TextNormalizer
      |
      +----------------------+
      |                      |
      v                      v
QuestionGrounding     QuestionExplanation


MAIN PURPOSE:

Normalize supporting facts before they are used for:
- grounding validation
- explanation generation

This module only cleans text.

It NEVER:
- generates questions
- changes meaning
- invents facts
- performs validation


INPUT:
Raw supporting fact string

OUTPUT:
Clean supporting fact string


CONNECTED MODULES:

Used by:
- question_grounding.py
- question_explanation.py

Dependencies:
- Python re module only


AUDIT STATUS:
CORE SHARED UTILITY
Changes affect multiple validation modules.
"""

import re


# ============================================================================
# TEXT NORMALIZATION CHECKPOINT
#
# Purpose:
# Convert raw extracted note fragments into clean supporting facts.
#
# Pipeline:
#
# Obsidian Note
#      |
#      v
# FactExtractor
#      |
#      v
# normalize_supporting_fact()
#      |
#      v
# Grounding / Explanation
#
# Responsibilities:
# - fix encoding artifacts
# - repair merged words
# - remove markdown
# - remove Obsidian syntax
# - normalize whitespace
# - reject obvious non-facts
#
# Important:
# This function should preserve the original meaning.
# It cleans formatting only.
#
# Connected:
# - question_grounding.py
# - question_explanation.py
# ============================================================================

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

    # Repair common UTF-8/Windows encoding artifacts that appear after
    # note extraction or file conversion.

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

    # Repair words accidentally joined together during extraction.
    # These corrections improve downstream grounding accuracy.

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

    # Remove Markdown and Obsidian formatting so only plain text remains.

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

    # Remove repetitive definition prefixes while preserving the factual content.
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


    # Reject headings, summaries, questions, and other note sections
    # that are not atomic factual statements.
    
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
