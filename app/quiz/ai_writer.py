"""
AI Writer Module - Orchestrates AI-based question generation.

This module is responsible ONLY for coordinating the generation pipeline.
It does not contain prompts, LLM calls, validation, scoring, or caching.

Responsibilities:
1. Receive normalized facts from the quiz pipeline
2. Request a prompt from prompt_builder
3. Send the prompt to llm_client
4. Parse the raw LLM response using llm_parser
5. Return parsed questions to the caller
"""

from typing import List, Dict, Any, Optional
from .prompt_builder import PromptBuilder
from .llm_client import LLMClient
from .llm_parser import LLMParser

# ============================================================================
# EXCEPTIONS
# ============================================================================


class AIWriterError(Exception):
    """Base exception for AI Writer errors."""

    pass


class LLMGenerationError(AIWriterError):
    """Raised when LLM generation fails."""

    pass


class ParsingError(AIWriterError):
    """Raised when response parsing fails."""

    pass


# ============================================================================
# MAIN CLASS
# ============================================================================


class AIWriter:
    """
    Orchestrates AI-based question generation.

    This class coordinates the pipeline:
        PromptBuilder → LLMClient → LLMParser

    It does not contain business logic, validation, or caching.
    """

    def __init__(
        self,
        model: str = "deepseek-r1:1.5b",
        temperature: float = 0.3,
        top_p: float = 0.8,
        num_predict: int = 800,
    ):
        """
        Initialize the AI Writer.

        Args:
            model: Ollama model name
            temperature: Sampling temperature (0.0-1.0)
            top_p: Nucleus sampling parameter
            num_predict: Maximum tokens to generate
        """
        self.prompt_builder = PromptBuilder()
        self.llm_client = LLMClient(model=model)
        self.parser = LLMParser()
        self.temperature = temperature
        self.top_p = top_p
        self.num_predict = num_predict

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def generate_from_fact(
        self, fact: str, answer: str, topic: str, num_predict: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a single question from a fact.

        Args:
            fact: The supporting fact text
            answer: The correct answer/concept
            topic: The topic name
            num_predict: Override max tokens (uses default if None)

        Returns:
            Parsed question dictionary, or None if generation failed

        Raises:
            LLMGenerationError: If the LLM fails to respond
            ParsingError: If the response cannot be parsed
        """
        # Step 1: Build the prompt
        prompt = self.prompt_builder.build_fact_prompt(fact, answer, topic)

        # Step 2: Call the LLM
        response = self._call_llm(prompt, num_predict)

        # Step 3: Parse the response
        result = self._parse_response(response)

        # Step 4: Extract questions
        questions = self.parser.extract_questions_from_result(result)

        if not questions:
            return None

        return questions[0]

    def generate_from_context(
        self, context: str, topic: str, num_predict: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate questions from a context block.

        Args:
            context: The content to generate questions from
            topic: The topic name
            num_predict: Override max tokens (uses default if None)

        Returns:
            List of parsed question dictionaries (may be empty)

        Raises:
            LLMGenerationError: If the LLM fails to respond
            ParsingError: If the response cannot be parsed
        """
        # Step 1: Build the prompt
        prompt = self.prompt_builder.build_context_prompt(context, topic)

        # Step 2: Call the LLM
        response = self._call_llm(prompt, num_predict)

        # Step 3: Parse the response
        result = self._parse_response(response)

        # Step 4: Extract questions
        return self.parser.extract_questions_from_result(result)

    def generate_fill_blank(
        self, context: str, topic: str, num_predict: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate fill-in-the-blank questions from context.

        Args:
            context: The content to generate questions from
            topic: The topic name
            num_predict: Override max tokens (uses default if None)

        Returns:
            List of parsed question dictionaries (may be empty)

        Raises:
            LLMGenerationError: If the LLM fails to respond
            ParsingError: If the response cannot be parsed
        """
        # Step 1: Build the prompt
        prompt = self.prompt_builder.build_fill_blank_prompt(context, topic)

        # Step 2: Call the LLM
        response = self._call_llm(prompt, num_predict)

        # Step 3: Parse the response
        result = self._parse_response(response)

        # Step 4: Extract questions
        return self.parser.extract_questions_from_result(result)

    # =========================================================================
    # PRIVATE HELPERS
    # =========================================================================

    def _call_llm(self, prompt: str, num_predict: Optional[int] = None) -> str:
        """
        Call the LLM with the given prompt.

        Args:
            prompt: The prompt to send
            num_predict: Override max tokens

        Returns:
            Raw LLM response text

        Raises:
            LLMGenerationError: If the LLM fails to respond
        """
        predict_tokens = num_predict or self.num_predict

        try:
            response = self.llm_client.generate(
                prompt=prompt,
                temperature=self.temperature,
                top_p=self.top_p,
                num_predict=predict_tokens,
            )

            if not response:
                raise LLMGenerationError("LLM returned empty response")

            return response

        except Exception as e:
            raise LLMGenerationError(f"LLM generation failed: {e}")

    def _parse_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parse the LLM response.

        Args:
            response: Raw LLM response text

        Returns:
            Parsed JSON result, or None if parsing fails

        Raises:
            ParsingError: If the response cannot be parsed
        """
        if not response:
            raise ParsingError("Empty response from LLM")

        try:
            result = self.parser.parse(response)

            if result is None:
                raise ParsingError("Failed to parse LLM response as JSON")

            return result

        except Exception as e:
            raise ParsingError(f"Response parsing failed: {e}")


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================


def generate_questions(
    fact: str,
    answer: str,
    topic: str,
    model: str = "deepseek-r1:1.5b",
    temperature: float = 0.3,
    top_p: float = 0.8,
    num_predict: int = 800,
) -> Optional[Dict[str, Any]]:
    """
    Convenience function for generating a single question from a fact.

    This is a thin wrapper around AIWriter for simpler use cases.

    Args:
        fact: The supporting fact text
        answer: The correct answer/concept
        topic: The topic name
        model: Ollama model name
        temperature: Sampling temperature
        top_p: Nucleus sampling parameter
        num_predict: Maximum tokens to generate

    Returns:
        Parsed question dictionary, or None if generation failed
    """
    writer = AIWriter(
        model=model, temperature=temperature, top_p=top_p, num_predict=num_predict
    )
    return writer.generate_from_fact(fact, answer, topic)
