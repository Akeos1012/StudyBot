"""
Question Prompt Module

Responsible for building LLM prompts for grounded question generation.
"""

def build_fact_question_prompt(
    fact: str,
    answer: str,
    topic: str,
    style_hint: str = None,
    question_type: str = None
) -> str:
    """
    Build a grounded multiple-choice question generation prompt.
    """
    return f"""
You are a computer science tutor. Create ONE grounded multiple-choice question.

FACT (Source of Truth):
{fact}

TARGET CONCEPT:
"{answer}"

TOPIC:
{topic}

RULES:
1. Grounding: The question must test "{answer}". The answer must appear in the FACT.
2. JSON ONLY: Return ONLY valid JSON. No markdown, no preambles, no explanations.
3. Structure: EXACTLY 4 options, labeled A), B), C), D).
4. Correctness: The 'correct' field must be the letter (e.g., "A").
5. Quality: Do NOT generate an explanation (leave empty).
6. Focus: Focus on the TARGET CONCEPT'S unique role or behavior. Do not ask for definitions.

REQUIRED JSON FORMAT:
{{
  "question": "Question text ending with ?",
  "options": ["A) {answer}", "B) Distractor 1", "C) Distractor 2", "D) Distractor 3"],
  "correct": "A",
  "explanation": ""
}}

Ensure valid JSON structure with exactly 4 options in the 'options' list.
"""
