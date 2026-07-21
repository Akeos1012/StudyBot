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

    # Remove concept mentions inside the definition
    text = re.sub(
        rf"\b{re.escape(concept)}\b",
        "",
        text,
        flags=re.IGNORECASE
    )

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

    # Restore grammar after removing concept
    if text.startswith(("A ", "An ", "The ")):
        text = text[0].lower() + text[1:]

    return f"_______ is {text}"