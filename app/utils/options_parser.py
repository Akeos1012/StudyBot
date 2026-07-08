# utils/options_parser.py
"""
Centralized option parsing utilities.
Single source of truth for all option text extraction.
"""

import re
from typing import List, Optional, Tuple

# ============ CORE PARSING FUNCTIONS ============

def extract_option_text(option: str) -> str:
    """
    Extract the text content from a formatted option.
    Handles various formats: "A) Text", "A. Text", "A - Text", "A Text"
    
    Args:
        option: Formatted option string (e.g., "A) Memoization")
    
    Returns:
        Clean text content (e.g., "Memoization")
    """
    if not option or not isinstance(option, str):
        return ""
    
    # Remove the letter prefix and any following separator
    # Pattern: Letter + optional separator ():.- ) + optional space + text
    match = re.match(r'^[A-D]\s*[\)\.\-\s]+\s*(.*)', option.strip())
    if match:
        return match.group(1).strip()
    
    # Fallback: split on common separators
    for separator in [')', '.', '-', '–']:
        if separator in option:
            parts = option.split(separator, 1)
            if len(parts) > 1:
                return parts[1].strip()
    
    # If no separator found, return the original
    return option.strip()


def extract_option_letter(option: str) -> str:
    """
    Extract the letter prefix from a formatted option.
    
    Args:
        option: Formatted option string (e.g., "A) Memoization")
    
    Returns:
        Letter (e.g., "A") or empty string if not found
    """
    if not option or not isinstance(option, str):
        return ""
    
    # Pattern: Letter at the start
    match = re.match(r'^([A-D])\s*[\)\.\-\s]', option.strip())
    if match:
        return match.group(1)
    
    # Fallback: check first character
    first_char = option.strip()[0] if option.strip() else ''
    if first_char in ['A', 'B', 'C', 'D']:
        return first_char
    
    return ""


def format_option(letter: str, text: str) -> str:
    """
    Format an option with consistent formatting.
    
    Args:
        letter: Option letter (A, B, C, D)
        text: Option text
    
    Returns:
        Formatted option (e.g., "A) Memoization")
    """
    return f"{letter}) {text}"


def extract_option_parts(option: str) -> Tuple[str, str]:
    """
    Extract both letter and text from a formatted option.
    
    Args:
        option: Formatted option string
    
    Returns:
        Tuple of (letter, text)
    """
    letter = extract_option_letter(option)
    text = extract_option_text(option)
    return letter, text


def get_correct_text_from_options(options: List[str], correct_letter: str) -> str:
    """
    Get the text of the correct option given its letter.
    
    Args:
        options: List of formatted options
        correct_letter: The correct letter (A, B, C, D)
    
    Returns:
        The text of the correct option, or empty string if not found
    """
    if not options or not correct_letter:
        return ""
    
    for opt in options:
        letter = extract_option_letter(opt)
        if letter == correct_letter:
            return extract_option_text(opt)
    
    return ""


def get_distractor_texts(options: List[str], correct_letter: str) -> List[str]:
    """
    Get the text of all distractors (non-correct options).
    
    Args:
        options: List of formatted options
        correct_letter: The correct letter (A, B, C, D)
    
    Returns:
        List of distractor texts
    """
    if not options:
        return []
    
    distractors = []
    for opt in options:
        letter = extract_option_letter(opt)
        if letter != correct_letter:
            text = extract_option_text(opt)
            if text:
                distractors.append(text)
    
    return distractors


def normalize_options(options: List[str]) -> List[str]:
    """
    Ensure all options are properly formatted with A), B), C), D).
    
    Args:
        options: List of options (may be mixed format)
    
    Returns:
        List of consistently formatted options
    """
    if not options:
        return []
    
    normalized = []
    for i, opt in enumerate(options):
        letter = chr(65 + i)  # A, B, C, D
        text = extract_option_text(opt)
        if not text:
            # If text extraction failed, use the original (strip any prefix)
            text = re.sub(r'^[A-D]\s*[\)\.\-\s]+', '', opt.strip())
        normalized.append(format_option(letter, text))
    
    return normalized


def options_to_dict(options: List[str]) -> dict:
    """
    Convert options list to a dictionary mapping letter -> text.
    
    Args:
        options: List of formatted options
    
    Returns:
        Dict like {'A': 'Text', 'B': 'Text', ...}
    """
    result = {}
    for opt in options:
        letter, text = extract_option_parts(opt)
        if letter and text:
            result[letter] = text
    return result


# ============ VALIDATION FUNCTIONS ============

def validate_options_format(options: List[str]) -> bool:
    """
    Check if options are properly formatted.
    
    Args:
        options: List of options
    
    Returns:
        True if all options start with A), B), C), D) respectively
    """
    if not options or len(options) != 4:
        return False
    
    for i, opt in enumerate(options):
        expected = f"{chr(65 + i)})"
        if not opt.startswith(expected):
            return False
    
    return True


def get_option_letter_at_index(index: int) -> str:
    """Get the letter for a given index (0->A, 1->B, etc.)"""
    if 0 <= index <= 3:
        return chr(65 + index)
    return ""


# ============ TEST ============

if __name__ == "__main__":
    test_options = [
        "A) Memoization",
        "B) Recursion",
        "C) Iteration",
        "D) Optimization"
    ]
    
    print("Testing options_parser.py")
    print("=" * 40)
    
    # Test extraction
    for opt in test_options:
        letter = extract_option_letter(opt)
        text = extract_option_text(opt)
        print(f"Input: '{opt}' → Letter: '{letter}', Text: '{text}'")
    
    # Test get_correct_text
    correct = get_correct_text_from_options(test_options, "A")
    print(f"\nCorrect text for 'A': '{correct}'")
    
    # Test distractors
    distractors = get_distractor_texts(test_options, "A")
    print(f"Distractors: {distractors}")
    
    # Test normalize
    mixed = ["A. Memoization", "B - Recursion", "C) Iteration", "D  Optimization"]
    normalized = normalize_options(mixed)
    print(f"\nNormalized: {normalized}")
    
    # Test options_to_dict
    as_dict = options_to_dict(test_options)
    print(f"\nAs dict: {as_dict}")
    
    print("\n✅ All tests passed!")