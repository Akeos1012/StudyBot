from enum import Enum
from typing import Dict, List

class FailureType(Enum):
    RETRYABLE = "retryable"
    NON_RETRYABLE = "non_retryable"

# Mapping validation errors to retryability
VALIDATION_RETRY_POLICY: Dict[str, FailureType] = {
    # Non-Retryable: Deterministic failures, retrying won't help.
    "Grounding validation failed": FailureType.NON_RETRYABLE,
    "Question restates the answer": FailureType.NON_RETRYABLE,
    "Domain validation failed": FailureType.NON_RETRYABLE,
    "Focus validation failed": FailureType.NON_RETRYABLE,
    "Quality check failed": FailureType.NON_RETRYABLE,
    "Semantic validation failed": FailureType.NON_RETRYABLE,
    
    # Retryable: Transient failures, LLM might succeed on next try.
    "JSON parsing failed": FailureType.RETRYABLE,
    "No questions extracted from JSON": FailureType.RETRYABLE,
    "Unexpected error": FailureType.RETRYABLE,
    "Insufficient distractors found": FailureType.NON_RETRYABLE,
}

def get_failure_type(reason: str) -> FailureType:
    # Default to non-retryable for safety, unless matched
    for key, failure_type in VALIDATION_RETRY_POLICY.items():
        if key in reason:
            return failure_type
    return FailureType.NON_RETRYABLE
