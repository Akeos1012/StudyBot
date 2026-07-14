# utils/__init__.py
"""Utility functions for the AI Study Companion."""

from ..quiz.options_parser import (
    extract_option_text,
    extract_option_letter,
    format_option,
    extract_option_parts,
    get_correct_text_from_options,
    get_distractor_texts,
    normalize_options,
    options_to_dict,
    validate_options_format,
    get_option_letter_at_index,
)

__all__ = [
    "extract_option_text",
    "extract_option_letter",
    "format_option",
    "extract_option_parts",
    "get_correct_text_from_options",
    "get_distractor_texts",
    "normalize_options",
    "options_to_dict",
    "validate_options_format",
    "get_option_letter_at_index",
]
