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

    print(f"\n❌ VALIDATION FAILED at stage: {stage}")
    print(f"   Reason: {reason}")


    # Record failure for metrics
    if _current_metrics:
        _current_metrics.add_failure(stage)


    if details:
        for key, value in details.items():
            print(f"   {key}: {value}")


    if question:
        print(
            f"   Question preview: "
            f"{question.get('question', 'N/A')[:80]}..."
        )

        print(
            f"   Options: {question.get('options', 'N/A')}"
        )

        print(
            f"   Correct: {question.get('correct', 'N/A')}"
        )

        print(
            f"   Concept: "
            f"{question.get('concept', 'N/A') or question.get('correct_text', 'N/A')}"
        )