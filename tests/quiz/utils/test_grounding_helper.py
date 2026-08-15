from app.quiz.utils.grounding_helper import get_canonical_grounding_context

def test_get_canonical_grounding_context():
    # 1. Continuation-style fact
    concept = "Deep Learning"
    fact = "is a branch of Artificial Intelligence."
    context = get_canonical_grounding_context(concept, fact)
    print(f"Case 1: '{context}'")
    assert context == "Deep Learning is a branch of Artificial Intelligence."

    # 2. Complete fact containing concept
    concept = "Cloud Storage"
    fact = "Cloud Storage allows users to store data remotely."
    context = get_canonical_grounding_context(concept, fact)
    print(f"Case 2: '{context}'")
    assert context == "Cloud Storage allows users to store data remotely."

    # 3. Case variation
    concept = "Deep Learning"
    fact = "IS A BRANCH OF ARTIFICIAL INTELLIGENCE."
    context = get_canonical_grounding_context(concept, fact)
    print(f"Case 3: '{context}'")
    assert context == "Deep Learning IS A BRANCH OF ARTIFICIAL INTELLIGENCE."

    # 4. Empty supporting fact
    concept = "Deep Learning"
    fact = ""
    context = get_canonical_grounding_context(concept, fact)
    print(f"Case 4: '{context}'")
    assert context == "Deep Learning"

    # 5. Empty concept
    concept = ""
    fact = "is a branch."
    context = get_canonical_grounding_context(concept, fact)
    print(f"Case 5: '{context}'")
    assert context == "is a branch."

test_get_canonical_grounding_context()
