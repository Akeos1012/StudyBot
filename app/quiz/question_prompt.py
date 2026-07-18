"""
Question Prompt Module

Responsible for building LLM prompts for grounded question generation.

Architecture Rule:
- Facts are the ONLY source of truth.
- LLM only transforms facts into question wording.
- LLM must never invent answers, concepts, or knowledge.
"""


def build_fact_question_prompt(
    fact: str, answer: str, topic: str, style_hint: str = None
) -> str:
    """
    Build a grounded multiple-choice question generation prompt.

    Args:
        fact: Extracted supporting fact from Fact Cache.
        answer: Target concept/correct answer.
        topic: Current topic.
        style_hint: Optional question style instruction.

    Returns:
        Prompt string for LLM.
    """

    style_instruction = ""

    if style_hint:
        style_instruction = f"""
STYLE HINT:
{style_hint}

Apply this style while keeping all grounding rules.
"""

    return f"""
You are a computer science tutor creating ONE grounded multiple-choice question.

You are NOT allowed to use outside knowledge.
You are NOT allowed to invent concepts.
The FACT provided below is the only source of truth.

FACT:
{fact}

TARGET CONCEPT (CORRECT ANSWER):
{answer}

TOPIC:
{topic}

{style_instruction}

Your task:
Convert the FACT into a clear multiple-choice question.

STRICT RULES:

1. The question must test the TARGET CONCEPT:
   "{answer}"

2. Do not ask for a direct definition.

   Bad:
   "What is Cloud Storage?"

   Bad:
   "Define Cloud Storage."

   Good:
   "Which cloud technology allows users to store files remotely over the internet?"

   Good:
   "Cloud Storage is primarily used for which purpose?"

   Good:
   "Which cloud service allows users to store digital files on remote servers?"

   The question may naturally mention the target concept.
   Avoid definition-style questions, not the concept name itself.

2.5 Question Focus Rules

   The question must clearly be about "{answer}".

   The reader should know which concept is being discussed before reading the answer choices.

   Whenever it sounds natural, include "{answer}" in the question itself.

   Avoid writing overly generic questions that could describe many different concepts.

   Good:
   Which cloud storage technology stores files on remote servers?

   Good:
   Cloud Storage is primarily designed for which purpose?

   Bad:
   Which technology stores files remotely?

   Bad:
   Which service manages data?

3. The question must be answerable ONLY using the FACT.

4. The correct answer option MUST be exactly:
   "{answer}"

5. The correct field MUST contain only the option letter:
   "A", "B", "C", or "D"

6. Return exactly 4 options:

   - Option A must be exactly "{answer}"
   - Options B, C, and D must be plausible but incorrect
   - Distractors must NOT be variations of the correct answer
   - Distractors must NOT introduce outside knowledge

7. Explanation requirements:

   - Explain why the answer is correct
   - Reference information from the FACT
   - Do not introduce new information

8. Vary the question opening.

Avoid using the same opening repeatedly.

Good openings include:

Vary the reasoning instead of merely varying the first words.

Questions may focus on:

• purpose
• function
• behavior
• characteristics
• role
• usage
• scenario
• identifying the concept from its behavior

Avoid relying on repetitive templates.

Do not repeatedly begin questions with:
- Which technology...
- Which service...
- Which concept...
- Which cloud service...

Write naturally, as if written by an experienced instructor.

Do not begin every question with "Which technology".

Avoid these patterns unless directly supported by the FACT:

- "What is the definition of..."
- "Which layer..."
- "Which component allows..."
- "Which service provides..."

9. Avoid generic questions:

   Bad:
   "Which concept is being described?"

   Bad:
   "What does this fact explain?"

10. Return ONLY valid JSON.
Do not include markdown.
Do not include explanations outside JSON.

Required JSON format:

{{
  "question": "Question text ending with ?",
  "options": [
    "A) {answer}",
    "B) Distractor",
    "C) Distractor",
    "D) Distractor"
  ],
  "correct": "A",
  "explanation": "Explanation based only on the FACT."
}}

FACT GROUNDING CHECK BEFORE OUTPUT:

Before returning JSON, verify:

- Is the answer exactly "{answer}"?
- Can the answer be found in the FACT?
- Does the explanation use the FACT?
- Are distractors incorrect according to the FACT?
- Does the question clearly identify "{answer}" as the subject being tested?
- Would a reader know which concept the question is about before looking at the answer choices?
- Is the wording specific rather than generic?

Generate exactly ONE question.
"""
