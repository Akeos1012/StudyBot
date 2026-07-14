"""
LLM Parser Module - Parses and normalizes LLM responses.

This module is responsible ONLY for:
- Extracting JSON from raw LLM text responses
- Removing markdown code fences (```json ... ```)
- Repairing malformed JSON using json_repair
- Converting parsed data into Python lists of dictionaries
- Normalizing field names to the internal schema

This module does NOT:
- Call Ollama or any HTTP APIs
- Build prompts
- Validate educational quality
- Generate fallback questions
- Modify question meaning

The output is clean Python objects ready for question_schema.py and quiz_validator.py.
"""

import json
import re
from typing import List, Dict, Any, Optional, Union
import logging

from json_repair import repair_json

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS
# ============================================================================

# Field name mappings: LLM output → internal schema
FIELD_NAME_MAPPING = {
    "choices": "options",
    "answer": "correct",
    "reason": "explanation",
    "correct_answer": "correct",
    "correct_option": "correct",
    "explanation": "explanation",
    "question_text": "question",
    "question_statement": "question",
}

# Expected field names in the internal schema
INTERNAL_FIELDS = {"question", "options", "correct", "explanation"}

# Markdown code fences to remove
CODE_FENCE_PATTERN = re.compile(r"^```(?:json)?\s*|\s*```$", flags=re.MULTILINE)


# ============================================================================
# EXCEPTIONS
# ============================================================================


class LLMParserError(Exception):
    """Base exception for parser errors."""

    pass


class JSONExtractionError(LLMParserError):
    """Raised when JSON cannot be extracted from the response."""

    pass


class JSONParsingError(LLMParserError):
    """Raised when JSON cannot be parsed or repaired."""

    pass


# ============================================================================
# MAIN PARSER CLASS
# ============================================================================


class LLMParser:
    """
    Parses and normalizes LLM responses.

    This class handles the extraction, cleaning, and normalization of
    JSON data from LLM responses. It returns clean Python objects ready
    for further processing.

    Usage:
        parser = LLMParser()
        result = parser.parse(response)
        questions = parser.extract_questions(result)
    """

    def __init__(self, strict_mode: bool = False):
        """
        Initialize the parser.

        Args:
            strict_mode: If True, raises exceptions on parse failures.
                         If False, returns None on failures.
        """
        self.strict_mode = strict_mode

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def parse(self, raw_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse raw LLM text into a Python dictionary.

        Args:
            raw_text: The raw text response from the LLM

        Returns:
            Parsed dictionary, or None if parsing fails (in non-strict mode)

        Raises:
            JSONExtractionError: If JSON cannot be extracted (strict mode)
            JSONParsingError: If JSON cannot be parsed (strict mode)
        """
        if not raw_text or not raw_text.strip():
            logger.warning("Empty response received")
            if self.strict_mode:
                raise JSONExtractionError("Empty response received")
            return None

        try:
            # Step 1: Extract JSON from the raw text
            json_str = self._extract_json(raw_text)

            if not json_str:
                logger.warning("No JSON found in response")
                if self.strict_mode:
                    raise JSONExtractionError("No JSON found in response")
                return None

            # Step 2: Remove markdown code fences
            json_str = self._remove_code_fences(json_str)

            # Step 3: Parse or repair the JSON
            result = self._parse_json(json_str)

            if result is None:
                logger.warning("Failed to parse JSON")
                if self.strict_mode:
                    raise JSONParsingError("Failed to parse JSON")
                return None

            return result

        except (JSONExtractionError, JSONParsingError):
            raise
        except Exception as e:
            logger.error(f"Unexpected parse error: {e}")
            if self.strict_mode:
                raise JSONParsingError(f"Unexpected parse error: {e}")
            return None

    def extract_questions(
        self, result: Union[Dict[str, Any], List[Dict[str, Any]], None]
    ) -> List[Dict[str, Any]]:
        """
        Extract and normalize questions from a parsed result.

        Args:
            result: The parsed result from parse()

        Returns:
            List of normalized question dictionaries (may be empty)
        """
        if not result:
            return []

        questions = self._extract_question_list(result)

        if not questions:
            logger.debug("No questions found in result")
            return []

        # Normalize each question
        normalized = []
        for q in questions:
            normalized_q = self._normalize_question(q)
            if normalized_q:
                normalized.append(normalized_q)

        return normalized

    # =========================================================================
    # PRIVATE METHODS
    # =========================================================================

    def _extract_json(self, raw_text: str) -> Optional[str]:
        """
        Extract JSON from raw text.

        Looks for content between braces or brackets. If multiple JSON objects
        are found, returns the first one.

        Args:
            raw_text: The raw text response

        Returns:
            Extracted JSON string, or None if not found
        """
        # Find JSON objects or arrays
        patterns = [
            r"\{[\s\S]*\}",  # JSON object
            r"\[[\s\S]*\]",  # JSON array
        ]

        for pattern in patterns:
            match = re.search(pattern, raw_text)
            if match:
                return match.group()

        return None

    def _remove_code_fences(self, json_str: str) -> str:
        """
        Remove markdown code fences from a JSON string.

        Args:
            json_str: The JSON string possibly wrapped in code fences

        Returns:
            Cleaned JSON string
        """
        return CODE_FENCE_PATTERN.sub("", json_str).strip()

    def _parse_json(self, json_str: str) -> Optional[Union[Dict[str, Any], List[Any]]]:
        """
        Parse a JSON string, with repair fallback.

        Args:
            json_str: The JSON string to parse

        Returns:
            Parsed dictionary, or None if parsing fails
        """
        # Try normal parse first
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            logger.debug("Normal JSON parse failed, attempting repair")

        # Try json_repair
        try:
            repaired = repair_json(json_str)
            return json.loads(repaired)
        except Exception as e:
            logger.debug(f"JSON repair failed: {e}")

        # Try manual cleaning
        try:
            cleaned = self._clean_json_manually(json_str)
            return json.loads(cleaned)
        except Exception as e:
            logger.debug(f"Manual JSON cleaning failed: {e}")

        return None

    def _clean_json_manually(self, json_str: str) -> str:
        """
        Apply manual fixes to a malformed JSON string.

        Args:
            json_str: The malformed JSON string

        Returns:
            Cleaned JSON string
        """
        cleaned = json_str

        # Replace single quotes with double quotes
        cleaned = cleaned.replace("'", '"')

        # Remove trailing commas in objects and arrays
        cleaned = re.sub(r",\s*}", "}", cleaned)
        cleaned = re.sub(r",\s*]", "]", cleaned)

        # Remove trailing commas after values in objects
        cleaned = re.sub(r'"\s*,\s*}', '"}', cleaned)

        return cleaned

    def _extract_question_list(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract a list of questions from a parsed result.

        Handles:
        - {"questions": [...]}
        - {"question": {...}}  (single question)
        - [...] (array of questions)

        Args:
            result: The parsed result

        Returns:
            List of question dictionaries
        """
        if not result:
            return []

        # Case 1: {"questions": [...]}
        if "questions" in result and isinstance(result["questions"], list):
            return result["questions"]

        # Case 2: {"question": {...}} or similar single question
        if "question" in result and isinstance(result["question"], dict):
            return [result["question"]]

        # Case 3: Check if the result itself looks like a question
        if self._looks_like_question(result):
            return [result]

        logger.debug("No question structure found in result")
        return []

    def _looks_like_question(self, data: Dict[str, Any]) -> bool:
        """
        Check if a dictionary looks like a question.

        Args:
            data: The dictionary to check

        Returns:
            True if it has question-like fields
        """
        required = ["question", "options", "correct"]
        return all(field in data for field in required)

    def _normalize_question(self, question: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Normalize a question dictionary to the internal schema.

        Args:
            question: The raw question dictionary

        Returns:
            Normalized question, or None if invalid
        """
        if not isinstance(question, dict):
            return None

        normalized = {}

        # Normalize each field
        for key, value in question.items():
            normalized_key = self._normalize_field_name(key)
            if normalized_key in INTERNAL_FIELDS:
                normalized[normalized_key] = self._normalize_field_value(
                    normalized_key, value
                )

        # Check minimum required fields
        if not all(field in normalized for field in ["question", "options", "correct"]):
            logger.debug(f"Question missing required fields: {question.keys()}")
            return None

        # Ensure options is a list
        if not isinstance(normalized.get("options"), list):
            logger.debug("Options field is not a list")
            return None

        return normalized

    def _normalize_field_name(self, field_name: str) -> str:
        """
        Normalize a field name to the internal schema.

        Args:
            field_name: The raw field name

        Returns:
            Normalized field name
        """
        return FIELD_NAME_MAPPING.get(field_name, field_name)

    def _normalize_field_value(self, field_name: str, value: Any) -> Any:
        """
        Normalize a field value based on its type.

        Args:
            field_name: The field name
            value: The raw value

        Returns:
            Normalized value
        """
        if field_name == "correct":
            # Normalize to uppercase letter
            if isinstance(value, str):
                # Handle "A)", "A.", "A -" patterns
                match = re.match(r"^([A-D])\s*[\)\.\-\s]", value.strip())
                if match:
                    return match.group(1)
                # Handle single letter
                if value.strip().upper() in {"A", "B", "C", "D"}:
                    return value.strip().upper()
            return value

        if field_name == "options" and isinstance(value, list):
            # Ensure options are strings
            return [str(opt).strip() for opt in value]

        if field_name == "question" and isinstance(value, str):
            # Strip whitespace
            return value.strip()

        return value


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


def parse_llm_response(raw_text: str) -> List[Dict[str, Any]]:
    """
    Convenience function: Parse raw LLM text into normalized questions.

    This is a thin wrapper around LLMParser for simple use cases.

    Args:
        raw_text: The raw LLM response text

    Returns:
        List of normalized question dictionaries (may be empty)
    """
    parser = LLMParser()
    result = parser.parse(raw_text)
    return parser.extract_questions(result)


def normalize_question(question: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Convenience function: Normalize a single question.

    Args:
        question: The raw question dictionary

    Returns:
        Normalized question, or None if invalid
    """
    parser = LLMParser()
    return parser._normalize_question(question)


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    # Test samples
    test_responses = [
        # Valid JSON
        '{"question": "What is SQL?", "options": ["A) SQL", "B) NoSQL"], "correct": "A"}',
        # With markdown
        '```json\n{"question": "What is SQL?", "options": ["A) SQL"], "correct": "A"}\n```',
        # With choices field
        '{"question": "What is SQL?", "choices": ["A) SQL", "B) NoSQL"], "answer": "A"}',
        # With extra text
        'Here is the question:\n{"question": "What is SQL?", "options": ["A) SQL", "B) NoSQL"], "correct": "A"}',
    ]

    parser = LLMParser()

    for i, response in enumerate(test_responses, 1):
        print(f"\n=== Test {i} ===")
        result = parser.parse(response)
        questions = parser.extract_questions(result)
        print(f"Parsed questions: {len(questions)}")
        for q in questions:
            print(f"  {q}")
