"""
Centralized option parsing utilities.

Single source of truth for all option text extraction, formatting, and normalization.
This module handles only the parsing, formatting, and validation of multiple-choice options.

Responsibilities:
- Extract letter and text from formatted options
- Format options consistently
- Normalize mixed-format options
- Validate option format
- Convert options to dictionary form

This module does NOT contain:
- Quiz generation logic
- Full question validation
- LLM functionality
- Business rules
"""

import re
from typing import List, Tuple, Dict


# ============================================================================
# CONSTANTS
# ============================================================================

# Valid option letters
OPTION_LETTERS = ["A", "B", "C", "D"]

# Common separators used in options
SEPARATORS = [')', '.', '-', '–']

# Compiled regex patterns for performance
LETTER_PATTERN = re.compile(r'^([A-D])\s*[\)\.\-\s]')
OPTION_PATTERN = re.compile(r'^[A-D]\s*[\)\.\-\s]+\s*(.*)')
PREFIX_PATTERN = re.compile(r'^[A-D]\s*[\)\.\-\s]+')


# ============================================================================
# CORE PARSING FUNCTIONS
# ============================================================================

def extract_option_parts(option: str) -> Tuple[str, str]:
    """
    Extract both letter and text from a formatted option.

    This is the SINGLE SOURCE OF TRUTH for option parsing.
    All other parsing functions delegate to this function.

    Args:
        option: Formatted option string (e.g., "A) Memoization")

    Returns:
        Tuple of (letter, text). Empty strings if parsing fails.

    Example:
        >>> extract_option_parts("A) Memoization")
        ('A', 'Memoization')
        >>> extract_option_parts("A. Memoization")
        ('A', 'Memoization')
        >>> extract_option_parts("A - Memoization")
        ('A', 'Memoization')
    """
    if not option or not isinstance(option, str):
        return "", ""

    option_stripped = option.strip()
    if not option_stripped:
        return "", ""

    # Try to match the full option pattern: letter + separator + text
    match = OPTION_PATTERN.match(option_stripped)
    if match:
        # Extract text content
        text = match.group(1).strip()
        # Extract letter using the letter pattern
        letter_match = LETTER_PATTERN.match(option_stripped)
        if letter_match:
            letter = letter_match.group(1)
            return letter, text

    # Fallback: split on common separators
    for sep in SEPARATORS:
        if sep in option_stripped:
            parts = option_stripped.split(sep, 1)
            if len(parts) > 1:
                # Try to extract letter from the first part
                first_part = parts[0].strip()
                letter_match = LETTER_PATTERN.match(first_part)
                if letter_match:
                    letter = letter_match.group(1)
                elif first_part in OPTION_LETTERS:
                    letter = first_part
                else:
                    letter = ""
                text = parts[1].strip()
                if letter:
                    return letter, text

    # If no separator found, check if the whole string is a letter
    if option_stripped in OPTION_LETTERS:
        return option_stripped, ""

    # Last resort: try to extract a letter from the start
    letter_match = LETTER_PATTERN.match(option_stripped)
    if letter_match:
        return letter_match.group(1), option_stripped[letter_match.end():].strip()

    return "", option_stripped


def extract_option_text(option: str) -> str:
    """
    Extract the text content from a formatted option.

    This is a convenience wrapper around extract_option_parts().

    Args:
        option: Formatted option string (e.g., "A) Memoization")

    Returns:
        Clean text content (e.g., "Memoization"), or empty string if not found.

    Example:
        >>> extract_option_text("A) Memoization")
        'Memoization'
    """
    _, text = extract_option_parts(option)
    return text


def extract_option_letter(option: str) -> str:
    """
    Extract the letter prefix from a formatted option.

    This is a convenience wrapper around extract_option_parts().

    Args:
        option: Formatted option string (e.g., "A) Memoization")

    Returns:
        Letter (e.g., "A") or empty string if not found.

    Example:
        >>> extract_option_letter("A) Memoization")
        'A'
    """
    letter, _ = extract_option_parts(option)
    return letter


def format_option(letter: str, text: str) -> str:
    """
    Format an option with consistent formatting.

    Args:
        letter: Option letter (A, B, C, D)
        text: Option text

    Returns:
        Formatted option (e.g., "A) Memoization")

    Example:
        >>> format_option("A", "Memoization")
        'A) Memoization'
    """
    return f"{letter}) {text}"


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_correct_text_from_options(options: List[str], correct_letter: str) -> str:
    """
    Get the text of the correct option given its letter.

    Args:
        options: List of formatted options
        correct_letter: The correct letter (A, B, C, D)

    Returns:
        The text of the correct option, or empty string if not found.

    Example:
        >>> options = ["A) Memoization", "B) Recursion", "C) Iteration", "D) Optimization"]
        >>> get_correct_text_from_options(options, "A")
        'Memoization'
    """
    if not options or not correct_letter:
        return ""

    correct_letter = correct_letter.strip().upper()
    for opt in options:
        letter, text = extract_option_parts(opt)
        if letter == correct_letter:
            return text

    return ""


def get_distractor_texts(options: List[str], correct_letter: str) -> List[str]:
    """
    Get the text of all distractors (non-correct options).

    Args:
        options: List of formatted options
        correct_letter: The correct letter (A, B, C, D)

    Returns:
        List of distractor texts.

    Example:
        >>> options = ["A) Memoization", "B) Recursion", "C) Iteration", "D) Optimization"]
        >>> get_distractor_texts(options, "A")
        ['Recursion', 'Iteration', 'Optimization']
    """
    if not options:
        return []

    correct_letter = correct_letter.strip().upper()
    distractors = []

    for opt in options:
        letter, text = extract_option_parts(opt)
        if letter and letter != correct_letter and text:
            distractors.append(text)

    return distractors


def normalize_options(options: List[str]) -> List[str]:
    """
    Ensure all options are properly formatted with A), B), C), D).

    Args:
        options: List of options (may be mixed format)

    Returns:
        List of consistently formatted options.

    Example:
        >>> normalize_options(["A. Memoization", "B - Recursion", "C) Iteration"])
        ['A) Memoization', 'B) Recursion', 'C) Iteration']
    """
    if not options:
        return []

    normalized = []
    for i, opt in enumerate(options):
        if i >= len(OPTION_LETTERS):
            break

        letter = OPTION_LETTERS[i]
        _, text = extract_option_parts(opt)

        if not text:
            # If text extraction failed, try to strip any prefix
            text = PREFIX_PATTERN.sub('', opt.strip())

        if text:
            normalized.append(format_option(letter, text))
        else:
            # If no text remains, use the original stripped of any prefix
            cleaned = PREFIX_PATTERN.sub('', opt.strip())
            if cleaned:
                normalized.append(format_option(letter, cleaned))
            else:
                normalized.append(format_option(letter, "Option"))

    return normalized


def options_to_dict(options: List[str]) -> Dict[str, str]:
    """
    Convert options list to a dictionary mapping letter -> text.

    Args:
        options: List of formatted options

    Returns:
        Dict like {'A': 'Text', 'B': 'Text', ...}

    Example:
        >>> options = ["A) Memoization", "B) Recursion"]
        >>> options_to_dict(options)
        {'A': 'Memoization', 'B': 'Recursion'}
    """
    result = {}
    for opt in options:
        letter, text = extract_option_parts(opt)
        if letter and text:
            result[letter] = text
    return result


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_options_format(options: List[str]) -> bool:
    """
    Check if options are properly formatted.

    Args:
        options: List of options

    Returns:
        True if all options start with A), B), C), D) respectively and are non-empty.

    Example:
        >>> validate_options_format(["A) Memoization", "B) Recursion", "C) Iteration", "D) Optimization"])
        True
        >>> validate_options_format(["A. Memoization", "B) Recursion"])
        False
    """
    if not options or len(options) != 4:
        return False

    for i, opt in enumerate(options):
        expected = f"{OPTION_LETTERS[i]})"
        if not opt.startswith(expected):
            return False
        # Ensure there's text after the prefix
        if len(opt) <= len(expected) + 1:
            return False

    return True


def get_option_letter_at_index(index: int) -> str:
    """
    Get the letter for a given index (0->A, 1->B, etc.).

    Args:
        index: The index (0-3)

    Returns:
        The letter, or empty string if index is out of range.

    Example:
        >>> get_option_letter_at_index(0)
        'A'
        >>> get_option_letter_at_index(3)
        'D'
        >>> get_option_letter_at_index(4)
        ''
    """
    if 0 <= index < len(OPTION_LETTERS):
        return OPTION_LETTERS[index]
    return ""


def is_valid_option_letter(letter: str) -> bool:
    """
    Check if a string is a valid option letter (A, B, C, or D).

    Args:
        letter: The string to check

    Returns:
        True if the string is a valid option letter, False otherwise.

    Example:
        >>> is_valid_option_letter("A")
        True
        >>> is_valid_option_letter("E")
        False
    """
    return letter.strip().upper() in OPTION_LETTERS