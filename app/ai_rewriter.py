import ollama

def polish_question(question: str, concept: str, definition: str) -> str:
    """
    Use AI only to polish the question wording.
    AI does NOT change the answer or invent facts.
    """
    prompt = f"""
    Rewrite this question to make it clearer and more natural.
    Do NOT change the meaning or the answer.
    Do NOT add new facts.

    Original: {question}

    Concept: {concept}
    Definition: {definition}

    Return ONLY the rewritten question.
    """

    try:
        response = ollama.chat(
            model="deepseek-r1:1.5b",
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.2, "num_predict": 100}
        )
        return response['message']['content'].strip()
    except:
        return question  # Fallback to original

if __name__ == "__main__":
    # Test
    polished = polish_question(
        "What is the definition of SQL?",
        "SQL",
        "SQL is a standard language for managing relational databases."
    )
    print(f"Original: What is the definition of SQL?")
    print(f"Polished: {polished}")