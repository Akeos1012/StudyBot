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
   "Which technology delivers computing resources such as storage, databases, networking, and software over the internet?"

   Good:
   "Cloud Computing provides users with what type of internet-based resources?"

   Good:
   "Which concept allows organizations to access computing services without relying only on local hardware?"

   The question may naturally mention the target concept.
   Avoid definition-style questions, not the concept name itself.

2.5 Question Focus Rules

Avoid using broader category terms in the question when they overlap with distractor choices.

Examples:
Bad:
"Which cloud storage technology uses fixed-size blocks?"
(Gives away a broader category and makes Cloud Storage appear correct)

Good:
"Which storage technology manages data in fixed-size units called blocks?"

The question must describe the unique property of the TARGET CONCEPT, not its parent category.

   The question must clearly be about "{answer}".

   The reader should know the TARGET CONCEPT is being described before reading the answer choices.

   Do not describe only a generic feature shared by many concepts.
   Use distinctive characteristics from the FACT that separate "{answer}" from related concepts.

   Example:

   TARGET CONCEPT:
   Cloud Computing

   Bad:
   "Which service allows users to store digital files on remote servers?"
   (This describes Cloud Storage, not the complete Cloud Computing concept.)

   Good:
   "Which technology provides computing resources such as storage, databases, and software over the internet?"

   For named concepts and technologies:

   Prefer identifying the TARGET CONCEPT using its unique characteristics.

   Include "{answer}" in the question only when necessary to avoid ambiguity.

   Do not replace the concept with a broader category.

   Examples:

   Bad:
   "Which cloud storage technology uses fixed-size blocks?"
   Reason:
   Cloud Storage is a broader category and could also match.

   Good:
   "Which cloud storage technology stores files in fixed-size units called blocks?"

   Bad:
   "Which service stores data remotely?"
   Reason:
   Multiple concepts can match.

   Good:
   "Which technology stores data as independent blocks that can be accessed separately?"
   - The question must still clearly identify "{answer}" and must not describe a broader category or a different concept.

   Avoid writing overly generic questions that could describe many different concepts.

   Good:
   Which technology stores digital files on remote servers instead of local devices?

   Good:
   Cloud Storage is primarily designed for which purpose?

   Bad:
   Which technology stores files remotely?

   Bad:
   Which service manages data?

3. The question must be answerable ONLY using the FACT.

4. One option must contain exactly:
   "{answer}"

   The option letter may be A, B, C, or D.

5. The correct field MUST contain only the option letter:
   "A", "B", "C", or "D"

6. Return exactly 4 options:

   - The correct option must contain exactly "{answer}".
   - The correct field must contain the letter of that option.
   - The correct answer position may be A, B, C, or D.
   - Options B, C, and D must be real concepts from the FACT or closely related concepts already implied by the FACT.
   - NEVER write placeholders.
   - NEVER write:
     "Distractor"
     "Distractor Option"
     "Option B"
     "Option C"
     "Option D"
     "None of the above"
     "Something else"

   If you cannot create valid distractors, return:

   {{
     "question": "",
     "options": [],
     "correct": "",
     "explanation": ""
   }}

   Distractors must be meaningful incorrect answers.

7. Explanation requirements:

   * Do NOT generate an explanation.
   * Return an empty string for the explanation field.
   * Explanation will be generated later from the supporting FACT by the grounding system.


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
