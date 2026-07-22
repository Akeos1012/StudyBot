import re
import logging

from .fill_blank_rules import build_fill_blank_question
from app.config import settings
from .question_explanation import build_consistent_explanation
logger = logging.getLogger(__name__)


class FillBlankGenerator:

    def _normalize_concept(self, text: str) -> str:
        return re.sub(
            r"[^a-z0-9]",
            "",
            text.lower()
        )

    def _force_replace_concept(
        self,
        text: str,
        concept: str
    ) -> str:

        pattern = re.compile(
            re.escape(concept),
            re.IGNORECASE
        )

        if pattern.search(text):
            text = pattern.sub("_______", text, count=1)

        return text

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

        # Normalize all blank styles to exactly 7 underscores
        text = re.sub(r'_{3,}', '_______', text)

        return text.strip()

    def __init__(self):
        self._generated_questions = []
        self._supporting_facts = []

    def generate_fill_blank(
        self,
        topic: str,
        supporting_facts: list = None
    ):
        self._supporting_facts = supporting_facts or []

        if not supporting_facts:
            logger.warning("No supporting facts provided.")
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

            word_count = len(definition.split())

            if word_count < 5 or definition.lower().strip() == concept.lower().strip():
                logger.warning(
                    "Fact too short or duplicate concept: %s",
                    concept
                )
                continue

            normalized_definition = definition.strip()

            question_text = build_fill_blank_question(
                concept,
                normalized_definition
            )

            question_text = self._force_replace_concept(
                question_text,
                concept
            )

            question_text = self._clean_question_text(question_text)

            # Remove duplicate blanks
            while question_text.count("_______") > 1:
                parts = question_text.split("_______")

                question_text = (
                    parts[0]
                    + "_______"
                    + "".join(parts[1:]).replace("_______", "")
                )

            question_text = self._clean_question_text(question_text)

            # Remove leaked concept from generated question
            concept_pattern = re.compile(
                re.escape(concept),
                re.IGNORECASE
            )

            if concept_pattern.search(question_text):

                logger.warning("Concept leaked. Attempting repair.")

                question_text = concept_pattern.sub(
                    "_______",
                    question_text
                )

            question_text = self._clean_question_text(question_text)

            question_text = self._clean_question_text(question_text)

            if question_text == definition:
                logger.warning("Concept was NOT replaced.")
                continue


            blank_count = question_text.count("_______")

            if blank_count != 1:
                logger.warning(
                    "Invalid blank count: %s",
                    blank_count
                )
                continue


            if not self._validate_blank_position(question_text):
                logger.warning("Invalid blank position.")
                continue


            if not self._validate_blank_replacement(
                question_text,
                concept
            ):
                logger.warning("Concept leaked into question.")
                continue


            quality = self._score_fill_blank_quality(
                {"question": question_text},
                concept
            )

            if not self._validate_fact_grounding(
                question_text,
                definition
            ):
                logger.warning("Question not grounded in fact.")
                continue

            if quality < 0.7:
                logger.warning(
                    "Fill blank quality too low: %.2f",
                    quality
                )
                continue


            logger.info(
                "Fill blank quality passed: %.2f",
                quality
            )

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

        text = question_text.lower()

        normalized_text = self._normalize_concept(text)
        normalized_concept = self._normalize_concept(concept)

        # Answer must not appear in question
        if normalized_concept in normalized_text:
            return False



        aliases = {
            "dombasedxss": [
                "dombasedcrosssitescripting",
                "domxss"
            ]
        }

        for key, values in aliases.items():
            if normalized_concept == key:
                for alias in values:
                    if alias in normalized_text:
                        return False


        # Detect concept variants after blank
        concept_variants = [
            concept.lower(),
            concept.lower().replace(" ", "-"),
            concept.lower().replace(" ", ""),
        ]

        for variant in concept_variants:
            if variant in text:
                return False

        # Blank should replace the actual concept, not random words
        before_blank = text.split("_______")[0]

        concept_words = concept.lower().split()

        # reject if sentence still contains parts of concept
        for word in concept_words:
            if len(word) > 3 and word in before_blank:
                return False

        return True

    def _validate_fact_grounding(
        self,
        question_text: str,
        definition: str
    ) -> bool:

        question_words = set(
            re.findall(
                r"\b[a-zA-Z]{4,}\b",
                question_text.lower()
            )
        )

        fact_words = set(
            re.findall(
                r"\b[a-zA-Z]{4,}\b",
                definition.lower()
            )
        )

        overlap = question_words.intersection(
            fact_words
        )

        return len(overlap) >= 3

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

            # Allow natural ending blanks.
            # Reject only extremely weak one-line questions.
            if len(text.split()) < 6:
                score -= 0.5

        return max(score, 0)