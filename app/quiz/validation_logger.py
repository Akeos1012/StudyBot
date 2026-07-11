
def log_validation_failure(question: dict, stage: str, reason: str, details: dict = None):
    """Log detailed validation failures for debugging."""
    print(f"\n❌ VALIDATION FAILED at stage: {stage}")
    print(f"   Reason: {reason}")
    
    if details:
        for key, value in details.items():
            print(f"   {key}: {value}")
    
    if question:
        print(f"   Question preview: {question.get('question', 'N/A')[:80]}...")
        print(f"   Options: {question.get('options', 'N/A')}")
        print(f"   Correct: {question.get('correct', 'N/A')}")
        print(f"   Concept: {question.get('concept', 'N/A') or question.get('correct_text', 'N/A')}")

