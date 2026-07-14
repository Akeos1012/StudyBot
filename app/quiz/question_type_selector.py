"""
Question Type Selector

Responsible only for selecting the question format
based on concept type.
"""

import random

from ..models.fact_schema import get_question_types_for_type


class QuestionTypeSelector:

    def __init__(self):

        self.type_weights = {
            "algorithm": {
                "definition": 0.25,
                "comparison": 0.25,
                "application": 0.25,
                "scenario": 0.15,
                "reverse_definition": 0.10,
            },
            "model": {
                "definition": 0.30,
                "comparison": 0.20,
                "application": 0.25,
                "scenario": 0.15,
                "reverse_definition": 0.10,
            },
            "concept": {
                "definition": 0.35,
                "comparison": 0.15,
                "application": 0.20,
                "scenario": 0.20,
                "reverse_definition": 0.10,
            },
            "system": {
                "definition": 0.25,
                "comparison": 0.20,
                "application": 0.30,
                "scenario": 0.15,
                "reverse_definition": 0.10,
            },
        }

    def select(self, concept_type: str, distractors: list[str]) -> str:

        recommended = get_question_types_for_type(concept_type)

        weights = self.type_weights.get(concept_type, self.type_weights["concept"])

        available = [q for q in weights if q in recommended]

        if len(distractors) < 2:
            if "comparison" in available:
                available.remove("comparison")

        if not available:
            return "definition"

        probabilities = [weights[q] for q in available]

        return random.choices(available, weights=probabilities)[0]
