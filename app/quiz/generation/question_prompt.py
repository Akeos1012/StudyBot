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
6. Focus: Questions must test understanding of the TARGET CONCEPT's function, role, behavior, application, or purpose.
   DO NOT generate questions that only ask for a definition (e.g., "What is [Concept]?").
   DO NOT generate questions where the question itself is just "What is [Concept]?" or equivalent.
   The question must test functional understanding or context (e.g., "How does [Concept] enable [Feature]?", "What is the primary role of [Concept] in [Process]?").
   Questions MUST be grounded in the fact provided.
   DO NOT invent information not supported by the FACT.

REQUIRED JSON FORMAT:
{{
  "question": "Question text ending with ?",
  "options": ["A) {answer}", "B) Distractor 1", "C) Distractor 2", "D) Distractor 3"],
  "correct": "A",
  "explanation": ""
}}

Ensure valid JSON structure with exactly 4 options in the 'options' list.
"""
