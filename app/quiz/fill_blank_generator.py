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

                    if (
                        "question" in q
                        and "correct" in q
                        and "_______" in q["question"]
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

                            q["_quality_score"] = 0.7

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
    1. The answer MUST be "{concept}".
    2. Create a question where the student fills in "{concept}".
    3. Use "_______" for the blank.
    4. The question must be based ONLY on the FACT.
    5. Do not add information outside the FACT.

    Return ONLY valid JSON:

    {{
    "questions": [
        {{
        "question": "Your question with _______ blank",
        "correct": "{concept}",
        "explanation": ""
        }}
    ]
    }}
    """