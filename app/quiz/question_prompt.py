def build_fact_question_prompt(
    fact: str,
    answer: str,
    topic: str
) -> str:

    return f"""You are a computer science tutor creating a multiple-choice question.

FACT: {fact}
CORRECT ANSWER: {answer}
TOPIC: {topic}

Requirements:
1. Question must end with "?"
2. Option A MUST be "{answer}" exactly
3. Correct field must be "A", "B", "C", or "D"
4. Explanation must reference the fact
5. All distractors must be plausible but incorrect
6. Return ONLY valid JSON

Example output:
{{
  "question": "What provides database services over the Internet instead of local storage systems?",
  "options": [
    "A) Cloud Database",
    "B) Local Storage",
    "C) Network Database",
    "D) Distributed Storage"
  ],
  "correct": "A",
  "explanation": "Cloud Database is correct because it provides database services over the Internet."
}}

Generate 5 different questions now:"""