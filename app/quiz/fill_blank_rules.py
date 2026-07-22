import re


def build_fill_blank_question(
    concept: str,
    definition: str
) -> str:

    text = definition.strip()

    # Remove concept prefix with separators
    text = re.sub(
        rf"^{re.escape(concept)}\s*[-–:]*\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    # Remove abbreviation leftovers like "(App Sec)"
    text = re.sub(
        r"^\([^)]*\)\s*",
        "",
        text
    )

    # Remove duplicated concept variants
    concept_words = concept.split()
    concept_pattern = r"\s+".join(
        map(re.escape, concept_words)
    )

    text = re.sub(
        rf"^{concept_pattern}\s*[-–:]*\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    # Remove concept mentions and known aliases inside the definition

    concept_aliases = [
        concept,
        concept.replace(" ", "-"),
        concept.replace("-", " "),
    ]

    # Known abbreviation patterns
    if "dom" in concept.lower() and "xss" in concept.lower():
        concept_aliases.extend([
            "DOM-based XSS",
            "DOM based XSS",
            "DOM XSS",
            "DOM-based Cross-Site Scripting",
            "DOM based Cross-Site Scripting",
        ])

    for alias in concept_aliases:
        text = re.sub(
            rf"\b{re.escape(alias)}\b",
            "",
            text,
            flags=re.IGNORECASE
        )

    # Remove empty parentheses left after alias removal
    text = re.sub(
        r"\(\s*\)",
        "",
        text
    )

    # Remove leftover separators
    text = re.sub(
        r"\s*[-–:]\s*",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    # Clean leftover punctuation
    text = re.sub(
        r"^\s*[-–:]\s*",
        "",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    # Restore grammar after blank
    grammar_patterns = [
        (
            r"^(practice|method|system|service|technology|model|process|security)\b",
            r"is a \1"
        ),
        (
            r"^(unique|random|cloud|physical|software|digital)\b",
            r"is a \1"
        ),
    ]

    for pattern, replacement in grammar_patterns:
        text = re.sub(
            pattern,
            replacement,
            text,
            flags=re.IGNORECASE
        )

    # Remove remaining concept variants
    concept_variants = [
        concept,
        concept.replace("-", " "),
        concept.replace(" ", "-"),
        concept.replace(" ", ""),
    ]

    for variant in concept_variants:
        text = re.sub(
            rf"\b{re.escape(variant)}\b",
            "",
            text,
            flags=re.IGNORECASE
        )

    # Clean spacing after removal
    text = re.sub(r"\s+", " ", text).strip()

    # Restore grammar after removing concept
    if text.startswith(("A ", "An ", "The ")):
        text = text[0].lower() + text[1:]

    # Remove dangling articles before verbs
    text = re.sub(
        r"^(a|an|the)\s+(refers to|means|is|are)\s+",
        r"\2 ",
        text,
        flags=re.IGNORECASE
    )

    # Avoid duplicate "is"
    if re.match(r"^(refers to|means|is|are)\b", text, re.IGNORECASE):
        return f"_______ {text}"

    return f"_______ is {text}"