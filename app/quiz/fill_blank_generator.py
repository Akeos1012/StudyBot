import json
import re
import time

from json_repair import repair_json

from .llm_parser import LLMParser
from app.config import settings
from .question_explanation import build_consistent_explanation


class FillBlankGenerator:

    def _clean_question_text(self, text: str) -> str:
        text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)

        replacements = {
            "computingand": "computing and",
            "organizationson-demand": "organizations on-demand",
            "handledby": "handled by",
            "systemswhere": "systems where",
            "cloud-basedinfrastructure": "cloud-based infrastructure",
            "anywhereusing": "anywhere using",
        }

        for bad, good in replacements.items():
            text = text.replace(bad, good)

        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def __init__(self, llm):
        self.llm = llm
        self.parser = LLMParser()
        self._generated_questions = []
        self._supporting_facts = []

    def generate_fill_blank(
        self,
        topic: str,
        supporting_facts: list = None
    ):
        self._supporting_facts = supporting_facts or []

        if not supporting_facts:
            print("⚠️ No supporting facts provided.")
            return {"questions": []}

        valid_questions = []

        for fact_data in supporting_facts[:settings.FILL_BLANK_FACT_LIMIT]:

            if not isinstance(fact_data, dict):
                continue

            concept = fact_data.get("concept", "").strip()

            definition = (
                fact_data.get("supporting_fact")
                or fact_data.get("definition")
                or fact_data.get("sentence")
                or ""
            )

            if not concept or not definition:
                continue

            normalized_definition = definition.strip()

            prompt = self._build_fill_blank_prompt(
                normalized_definition,
                concept,
                topic
            )

            try:
                content = self.llm.generate(prompt)

                result = self.parser.parse(content)

                if not result:
                    print("❌ Fill blank JSON parse failed")
                    continue

                questions = self.parser.extract_questions(result)

                if not questions:
                    print("❌ No fill blank question returned")
                    continue

                question_text = questions[0].get(
                    "question",
                    ""
                ).strip()

            except Exception as e:
                print(
                    "❌ Fill blank generation failed:",
                    e
                )
                continue

            question_text = self._clean_question_text(question_text)

            print("\n===== FILL BLANK DEBUG =====")
            print("Concept:", concept)
            print("Original:")
            print(definition)
            print("Generated:")
            print(question_text)
            print("============================")

            question_text = self._clean_question_text(question_text)

            if question_text == definition:
                print("❌ Concept was NOT replaced.")
                continue
            else:
                print("✅ Concept replaced successfully.")

            explanation = build_consistent_explanation(
                question_text,
                [],
                "",
                concept,
                context=definition,
                facts=[fact_data],
            )

            q = {
                "question": question_text,
                "correct": concept,
                "correct_text": concept,
                "explanation": explanation,
                "type": "fill_blank",
                "supporting_fact": definition,
                "concept": concept,
                "source_note": fact_data.get(
                    "source_note",
                    "inline"
                ),
                "fact_id": fact_data.get(
                    "fact_id",
                    f"fillblank_{concept}"
                ),
            }

            valid_questions.append(q)


        self._generated_questions.extend(valid_questions)

        return {
            "questions": valid_questions
        }

    def _validate_blank_position(
        self,
        question_text: str
    ) -> bool:

        text = question_text.strip().lower()

        if not text:
            return False

        # Reject fragments where the subject was removed
        bad_starts = [
            "is a ",
            "refers to ",
            "are ",
            "was ",
            "means "
        ]

        for bad in bad_starts:
            if text.startswith(bad):
                return False

        return True

    def _validate_blank_replacement(
        self,
        question_text: str,
        concept: str
    ) -> bool:

        normalized = question_text.lower()
        concept_lower = concept.lower()

        # Multi-word concepts must not leave partial words behind
        concept_words = concept_lower.split()

        for word in concept_words:
            if word in normalized:
                return False

        return True

    def _score_fill_blank_quality(self, question, concept):
        score = 1.0

        text = question.get("question", "").lower()

        if "replace the answer" in text:
            score -= 0.3

        if "following statement" in text:
            score -= 0.2

        if concept.lower() in text:
            score -= 0.3

        if "_______" not in text:
            score -= 0.5

        if text.rstrip(".!?").endswith("_______"):
            score -= 0.5

        return max(score, 0)

    def _build_fill_blank_prompt(
        self,
        definition: str,
        concept: str,
        topic: str
    ):
        safe_topic = str(topic).strip() if topic else "Unknown"

        return f"""You are a computer science tutor creating a fill-in-the-blank question.

    CONCEPT: {concept}
    FACT: {definition}
    TOPIC: {safe_topic}


Requirements:

    1. The answer MUST be exactly "{concept}".

    2. Create a natural fill-in-the-blank question using the FACT as the source.

    3. The blank must represent the entire concept "{concept}", not a word inside the concept.

    4. Keep the question fully grounded in the FACT. Do not add outside information.

    5. Rewrite the sentence if needed so the blank appears in a natural position.

    6. The question should test recognition of the concept, not simply remove the concept name from the original sentence.

    7. Do NOT create blanks like:
       - "its _______"
       - "the _______ of"
       - "known as _______"
       - "what term describes _______"

    8. Preserve the original meaning and technical accuracy.

    9. Preserve normal spacing between every word.

    Return ONLY valid JSON:

    {{
    "questions": [
        {{
        "question": "",
        "correct": "{concept}",
        "explanation": ""
        }}
    ]
    }}
    """
