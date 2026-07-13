"""
LLM Client Module - Reusable communication layer for LLM interactions.

This module is responsible ONLY for sending requests to the LLM and returning
raw text responses. It does NOT contain:
- Prompt templates
- Question generation logic
- Question polishing logic
- Parsing or validation
- Business logic of any kind

This module is reusable by any future AI feature including:
- Question generation
- Question polishing
- Explanation generation
- Hint generation
- Summarization
"""

import ollama
from typing import List, Dict, Any, Optional
import logging

# Configure module logger
logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS
# ============================================================================

DEFAULT_MODEL = "deepseek-r1:1.5b"
DEFAULT_TEMPERATURE = 0.3
DEFAULT_TOP_P = 0.8
DEFAULT_NUM_PREDICT = 800


# ============================================================================
# EXCEPTIONS
# ============================================================================

class LLMClientError(Exception):
    """Base exception for LLM client errors."""
    pass


class LLMConnectionError(LLMClientError):
    """Raised when unable to connect to the LLM service."""
    pass


class LLMResponseError(LLMClientError):
    """Raised when the LLM returns an invalid or empty response."""
    pass


# ============================================================================
# MAIN CLASS
# ============================================================================

class LLMClient:
    """
    A reusable client for communicating with Ollama LLM.
    
    This class handles the low-level communication with the LLM service.
    It does not contain any business logic, prompt construction, or
    response parsing.
    
    Usage:
        client = LLMClient(model="deepseek-r1:1.5b")
        response = client.generate("What is the capital of France?")
        
        # Or with custom options
        response = client.generate(
            prompt="Explain quantum computing",
            temperature=0.7,
            num_predict=500
        )
        
        # Or with chat-style messages
        response = client.chat([
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is Python?"}
        ])
    """
    
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        top_p: float = DEFAULT_TOP_P,
        num_predict: int = DEFAULT_NUM_PREDICT,
        timeout: Optional[int] = 30
    ):
        """
        Initialize the LLM client.
        
        Args:
            model: The Ollama model name to use
            temperature: Sampling temperature (0.0-1.0)
            top_p: Nucleus sampling parameter
            num_predict: Maximum tokens to generate
            timeout: Request timeout in seconds (optional)
        """
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.num_predict = num_predict
        self.timeout = timeout
    
    def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        num_predict: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Send a prompt to the LLM and return the raw text response.
        
        Args:
            prompt: The prompt text to send
            temperature: Override default temperature
            top_p: Override default top_p
            num_predict: Override default num_predict
            **kwargs: Additional options passed to ollama.chat
        
        Returns:
            The raw text response from the LLM
        
        Raises:
            LLMConnectionError: If unable to connect to the LLM service
            LLMResponseError: If the LLM returns an empty or invalid response
        """
        messages = [{"role": "user", "content": prompt}]
        return self.chat(
            messages,
            temperature=temperature,
            top_p=top_p,
            num_predict=num_predict,
            **kwargs
        )
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        num_predict: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Send a chat conversation to the LLM and return the raw text response.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
                     Example: [{"role": "user", "content": "Hello"}]
            temperature: Override default temperature
            top_p: Override default top_p
            num_predict: Override default num_predict
            **kwargs: Additional options passed to ollama.chat
        
        Returns:
            The raw text response from the LLM
        
        Raises:
            LLMConnectionError: If unable to connect to the LLM service
            LLMResponseError: If the LLM returns an empty or invalid response
        """
        if not messages:
            raise LLMResponseError("Messages list cannot be empty")
        
        options = self._build_options(
            temperature,
            top_p,
            num_predict,
            **kwargs
        )
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=messages,
                options=options
            )
        except Exception as e:
            logger.error(f"LLM connection error: {e}")
            raise LLMConnectionError(f"Failed to connect to LLM: {e}")
        
        if not response:
            raise LLMResponseError("LLM returned an invalid response format")

        if hasattr(response, "message"):
            content = response.message.content

        elif isinstance(response, dict):
            content = response.get("message", {}).get("content", "")

        else:
            raise LLMResponseError("Unknown LLM response format")
        
        if not content:
            raise LLMResponseError("LLM returned an empty response")
        
        return content.strip()
    
    # =========================================================================
    # PRIVATE HELPERS
    # =========================================================================
    
    def _build_options(
        self,
        temperature: Optional[float],
        top_p: Optional[float],
        num_predict: Optional[int],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Build the options dict for ollama.chat.
        
        Args:
            temperature: Override temperature, or None to use default
            top_p: Override top_p, or None to use default
            num_predict: Override num_predict, or None to use default
        
        Returns:
            Dictionary of options for ollama.chat
        """
        options = {}
        
        if temperature is not None:
            options["temperature"] = temperature
        else:
            options["temperature"] = self.temperature
        
        if top_p is not None:
            options["top_p"] = top_p
        else:
            options["top_p"] = self.top_p
        
        if num_predict is not None:
            options["num_predict"] = num_predict
        else:
            options["num_predict"] = self.num_predict

        # Additional Ollama options
        options.update(kwargs)
        
        return options


    
    
    
    # =========================================================================
    # CONVENIENCE METHODS
    # =========================================================================
    
    def generate_with_system(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        num_predict: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Send a prompt with a system message to the LLM.
        
        Args:
            system_prompt: The system instruction
            user_prompt: The user prompt
            temperature: Override default temperature
            top_p: Override default top_p
            num_predict: Override default num_predict
            **kwargs: Additional options
        
        Returns:
            The raw text response from the LLM
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        return self.chat(messages, temperature, top_p, num_predict, **kwargs)


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def generate(
    prompt: str,
    model: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    top_p: float = DEFAULT_TOP_P,
    num_predict: int = DEFAULT_NUM_PREDICT
) -> str:
    """
    Convenience function for a simple one-off LLM request.
    
    This is a thin wrapper around LLMClient for quick, simple use cases.
    
    Args:
        prompt: The prompt text to send
        model: The Ollama model to use
        temperature: Sampling temperature
        top_p: Nucleus sampling parameter
        num_predict: Maximum tokens to generate
    
    Returns:
        The raw text response from the LLM
    
    Raises:
        LLMConnectionError: If unable to connect to the LLM
        LLMResponseError: If the LLM returns an empty response
    """
    client = LLMClient(
        model=model,
        temperature=temperature,
        top_p=top_p,
        num_predict=num_predict
    )
    return client.generate(prompt)


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    # Test basic generation
    print("Testing LLMClient...")
    
    client = LLMClient()
    
    try:
        response = client.generate("What is the capital of France?")
        print(f"Response: {response}")
    except LLMClientError as e:
        print(f"Error: {e}")