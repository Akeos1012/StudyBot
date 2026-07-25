"""
Question Prompt Module

Responsible for building LLM prompts for grounded question generation.

Architecture Rule:
- Facts are the ONLY source of truth.
- LLM only transforms facts into question wording.
- LLM must never invent answers, concepts, or knowledge.
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

    Args:
        fact: Extracted supporting fact from Fact Cache.
        answer: Target concept/correct answer.
        topic: Current topic.
        style_hint: Optional question style instruction.

    Returns:
        Prompt string for LLM.
    """

    style_instruction = ""

    question_type_instruction = ""

    if question_type:
      type_rules = {
        "definition": """
Create a question that tests the meaning or purpose of the concept.
Focus on what the concept does, not a dictionary definition.

Example:
"Which service allows users to store files remotely through internet-based infrastructure?"
""",

        "comparison": """
Create a question that requires distinguishing the TARGET CONCEPT from another related concept.

The question must compare properties, behavior, purpose, or usage.

Example:
"How does object storage differ from traditional file storage?"
""",

        "application": """
Create a question where the learner must apply the concept to a practical situation.

Do not ask what the concept is.
Ask when or how it should be used.

Example:
"A company needs scalable storage without maintaining physical servers. Which concept fits this requirement?"
""",

        "scenario": """
Create a realistic situation where the learner identifies the correct concept.

The question should describe a problem or environment.

Example:
"A developer wants users to access files from multiple devices without local storage. What technology is being used?"
""",

        "relationship": """
Create a question about how this concept connects with another concept mentioned in the FACT.

Focus on dependency, interaction, or role.

Example:
"How does cloud storage support applications running in cloud environments?"
""",

        "recognition": """
Create a question where the learner identifies the concept from unique characteristics.

Do not mention the concept name directly.

Example:
"Which technology stores data as independent objects with metadata?"
""",

        "cause_effect": """
Create a question that tests why something happens or what result occurs.

Focus on reasoning, not memorization.

Example:
"Why do organizations use cloud databases instead of maintaining local database servers?"
""",

        "classification": """
Create a question where the learner identifies the category or type of the concept.

Example:
"Which category does this storage method belong to based on its behavior?"
""",

"error_detection": """
Create an error detection question.

The question should present a statement, process, or situation
related only to the FACT.

Ask the learner to identify what is incorrect, missing, or
misunderstood.

The incorrect element must be based on the FACT.
Do not invent errors using outside knowledge.

Example pattern:
"Which statement about [concept] contains an error?"
"Which explanation incorrectly describes [concept]?"
""",

    }

    question_type_instruction = f"""
QUESTION TYPE:
{question_type}

Follow this cognitive pattern:

{type_rules.get(question_type.lower(), "")}

IMPORTANT:
The question type must change the reasoning task.
Do not only rewrite the wording.

A {question_type} question must feel different from a definition question.
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
{question_type_instruction}


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

The question must focus ONLY on the TARGET CONCEPT.

Rules:

- Do not use information from related concepts.
- Do not combine properties from different concepts.
- Do not mention distractor concepts inside the question unless the FACT itself explains a relationship.

The question must describe the unique characteristics of:

"{answer}"

Examples:

TARGET:
Block Storage

Bad:
"Which cloud storage technology uses fixed-size blocks?"
Reason:
This mixes Cloud Storage with Block Storage.

Good:
"Which storage method organizes data into independent fixed-size blocks that can be accessed separately?"

---

TARGET:
Cloud Storage

Bad:
"Which technology stores data in fixed-size blocks?"
Reason:
This describes Block Storage.

Good:
"Which service stores digital files on remote servers and allows access through the internet?"

---

TARGET:
Cloud Database

Bad:
"Which technology stores data remotely like cloud services?"
Reason:
Too broad.

Good:
"Which service manages databases through cloud infrastructure instead of local servers?"

---

Before generating the question:

1. Identify the unique property of "{answer}" from the FACT.
2. Remove properties belonging to other concepts.
3. Build the question using only those unique properties.

The reader should be able to identify the TARGET CONCEPT before seeing the answer choices.

Do not create comparison questions.
Do not create "similar to" questions.
Do not mention broader categories that can match multiple answers.

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
