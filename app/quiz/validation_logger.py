import logging

logger = logging.getLogger(__name__)

_current_metrics = None


def set_metrics(metrics):
    """
    Attach current quiz metrics tracker.
    """

    global _current_metrics

    _current_metrics = metrics


def get_metrics():
    """
    Retrieve current quiz metrics tracker.
    """

    return _current_metrics



def log_validation_failure(
    question: dict,
    stage: str,
    reason: str,
    details: dict = None
):
    """
    Log detailed validation failures for debugging
    and record metrics.
    """

    logger.debug(f"VALIDATION FAILED | Stage: {stage}")
    logger.debug(f"Reason: {reason}")


    # Record failure for metrics
    if _current_metrics:
        _current_metrics.add_failure(stage)


    if details:
        for key, value in details.items():
            logger.debug(f"{key}: {value}")


    if question:
        logger.debug(
            f"Question: {question.get('question', 'N/A')[:80]}..."
        )

        logger.debug(
            f"Options: {question.get('options', 'N/A')}"
        )

        logger.debug(
            f"Correct: {question.get('correct', 'N/A')}"
        )

        logger.debug(
            f"Concept: {question.get('concept', 'N/A') or question.get('correct_text', 'N/A')}"
        )