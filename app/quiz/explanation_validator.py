def validate_explanation(question: dict, supporting_fact: str) -> bool:
    explanation = question.get("explanation", "").lower()

    if not explanation:
        return False

    fact_words = set(supporting_fact.lower().split())

    explanation_words = set(explanation.split())

    overlap = fact_words.intersection(explanation_words)

    if len(overlap) < 2:
        print("⚠️ Explanation not grounded in fact")
        return False

    return True
