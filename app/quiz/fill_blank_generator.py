import json
import re
import time

from json_repair import repair_json

from app.config import settings
from .question_explanation import build_consistent_explanation


class FillBlankGenerator:

    def __init__(self, llm):
        self.llm = llm
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

            concept = (
                fact_data.get("concept")
                or fact_data.get("answer")
                or ""
            )

            definition = (
                fact_data.get("supporting_fact")
                or fact_data.get("definition")
                or fact_data.get("sentence")
                or ""
            )

            if not concept or not definition:
                continue

            prompt = self._build_fill_blank_prompt(
                definition,
                concept,
                topic
            )

            try:
                start_time = time.time()

                content = self.llm.generate(
                    prompt,
                    temperature=settings.LLM_TEMPERATURE,
                    top_p=settings.LLM_TOP_P,
                    num_predict=settings.LLM_NUM_PREDICT
                )

                print(
                    f"Fill blank response: {len(content)} chars"
                )

                print("RAW RESPONSE:")
                print(content)

                json_match = re.search(
                    r'\{[\s\S]*\}',
                    content
                )

                if not json_match:
                    continue

                repaired = repair_json(
                    json_match.group()
                )

                import json
                result = json.loads(repaired)

                for q in result.get("questions", []):

                    question_text = q["question"].strip()

                    if (
                        "question" in q
                        and "correct" in q
                        and "_______" in question_text
                        and "replace the answer" not in question_text.lower()
                        and "following statement" not in question_text.lower()
                        and "complete sentence" not in question_text.lower()
                        and "answer removed" not in question_text.lower()
                        and "answer replaced" not in question_text.lower()
                        and not question_text.rstrip(".!?").endswith("_______")
                    ):

                        if q["correct"].lower() == concept.lower():

                            q["supporting_fact"] = definition
                            q["concept"] = concept
                            q["source_note"] = fact_data.get(
                                "source_note",
                                "inline"
                            )

                            q["fact_id"] = fact_data.get(
                                "fact_id",
                                f"fillblank_{concept}"
                            )

                            q["explanation"] = build_consistent_explanation(
                                question_text=q["question"],
                                options=[concept],
                                correct_letter="A",
                                correct_text=concept,
                                context=definition,
                                facts=[fact_data]
                            )

                            q["_quality_score"] = self._score_fill_blank_quality(q, concept)

                            valid_questions.append(q)

                if valid_questions:
                    break

            except Exception as e:
                print(
                    f"⚠️ Fill blank generation failed: {e}"
                )

        self._generated_questions.extend(valid_questions)

        return {
            "questions": valid_questions
        }

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
    2. Replace the concept "{concept}" inside the sentence with "_______".
    3. The blank must appear where the answer belongs, NOT at the end of the sentence.
    4. The question must test understanding of the FACT only.
    5. Do not add information outside the FACT.
    6. Make the sentence grammatically correct after removing the concept.

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