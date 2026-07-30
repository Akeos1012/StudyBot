"""
MODULE: Validation Logger

LOCATION:
app/quiz/validation_logger.py


PIPELINE POSITION:

Question Validation
        |
        +----------------------+
        |                      |
        v                      v
Validation Logger      Quiz Metrics
        |
        v
Debug Logs


MAIN PURPOSE:

Provide centralized logging for validation failures.

This module records:
- rejection reason
- validation stage
- failed question
- metrics

It does NOT:
- validate questions
- modify questions
- generate questions


INPUT:
Validation failure information

OUTPUT:
- Log messages
- Updated quiz metrics


CONNECTED MODULES:

Used by:
- quiz_generator.py
- question_validator.py
- question_grounding.py
- question_semantic.py
- domain_validator.py

Connected to:
- quiz_metrics.py


AUDIT STATUS:
SHARED LOGGING UTILITY
Changing behavior affects every validation module.
"""

import logging

logger = logging.getLogger(__name__)

# ============================================================================
# GLOBAL METRICS TRACKER
#
# Stores the active QuizMetrics instance so every validation
# module can report failures without directly depending on
# QuizMetrics.
#
# Acts as a shared reporting channel.
# ============================================================================

_current_metrics = None

def set_metrics(metrics):
    """
    Attach current quiz metrics tracker.
    """

    global _current_metrics

    _current_metrics = metrics

def get_metrics(metrics_context=None):
    """
    Retrieve current quiz metrics tracker.
    """
    if metrics_context:
        return metrics_context.quiz_metrics

    return _current_metrics

# ============================================================================
# VALIDATION FAILURE CHECKPOINT
#
# Central logging function for every rejected question.
#
# Responsibilities:
# - record rejection stage
# - record rejection reason
# - update QuizMetrics
# - write debug information
#
# Pipeline:
#
# Validation Module
#        |
#        v
# log_validation_failure()
#        |
#        +--> Logger
#        |
#        +--> QuizMetrics
#
# Important:
# This function never rejects questions itself.
# It only records why another module rejected them.
#
# Connected:
# - question_validator.py
# - question_grounding.py
# - question_semantic.py
# - domain_validator.py
# - quiz_generator.py
# ============================================================================

def log_validation_failure(
    question: dict,
    stage: str,
    reason: str,
    details: dict = None,
    metrics_context=None
):
    """
    Log detailed validation failures for debugging
    and record metrics.
    """

    logger.warning(f"VALIDATION FAILED | Stage: {stage}")
    logger.warning(f"Reason: {reason}")

    # Record failure for metrics
    metrics = get_metrics(metrics_context)
    if metrics:
        metrics.add_failure(stage)


    if details:
        for key, value in details.items():
            logger.debug(f"{key}: {value}")


    if question:
        logger.warning(
            f"Question: {question.get('question', 'N/A')[:80]}..."
        )

        logger.warning(
            f"Options: {question.get('options', 'N/A')}"
        )

        logger.debug(
            f"Correct: {question.get('correct', 'N/A')}"
        )

        logger.debug(
            f"Concept: {question.get('concept', 'N/A') or question.get('correct_text', 'N/A')}"
        )