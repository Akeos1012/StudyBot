import pytest
from app.quiz.utils.grounding_helper import get_canonical_grounding_context
from app.quiz.validation.question_grounding import validate_grounding

def test_grounding_context_builder():
    # 1. Continuation-style fact
    concept = "Deep Learning"
    fact = "is a branch of Artificial Intelligence."
    context = get_canonical_grounding_context(concept, fact)
    assert context == "Deep Learning is a branch of Artificial Intelligence."

    # 2. Complete fact containing concept
    concept = "Cloud Storage"
    fact = "Cloud Storage allows users to store data remotely."
    context = get_canonical_grounding_context(concept, fact)
    assert context == "Cloud Storage allows users to store data remotely."

    # Test Grounding Validation with these contexts
    # Case: continuation fact (should now PASS)
    q = {"correct": "A", "options": ["A) Deep Learning", "B) B"], "concept": "Deep Learning"}
    assert validate_grounding(q, "", supporting_fact=fact) is True

    # Case: unrelated fact (should fail)
    q = {"correct": "A", "options": ["A) Deep Learning", "B) B"], "concept": "Deep Learning"}
    # Using a fact that definitely does not contain the answer
    unrelated_fact = "The sky is blue."
    assert validate_grounding(q, "", supporting_fact=unrelated_fact) is False
