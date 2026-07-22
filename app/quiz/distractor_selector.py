from typing import List, Dict, Any
import random


class DistractorSelector:


    def _is_related_concept(
        self,
        concept: str,
        target_concept: str
    ) -> bool:
        """
        Reject distractors that are too closely related
        to the correct answer.
        """

        a = concept.lower()
        b = target_concept.lower()

        # exact match
        if a == b:
            return True

        # shared important words
        a_words = set(a.replace("-", " ").split())
        b_words = set(b.replace("-", " ").split())

        common = a_words & b_words

        if common:
            return True

        return False

    def get_compatible_facts(
        self,
        facts: List[Dict[str, Any]],
        target_fact: Dict[str, Any]
    ):
        target_concept = target_fact.get("concept")
        target_type = target_fact.get("concept_type")

        candidates = []

        for fact in facts:

            concept = fact.get("concept")

            if not concept:
                continue

            # remove same or related answer
            if self._is_related_concept(
                concept,
                target_concept
            ):
                continue
            
            # same ontology type only
            if fact.get("concept_type") != target_type:
                continue

            candidates.append(fact)

        return candidates


    def select_distractors(
        self,
        facts,
        target_fact,
        count=3,
    ):
        compatible = self.get_compatible_facts(
            facts,
            target_fact,
        )

        distractors = []

        random.shuffle(compatible)

        for fact in compatible:

            concept = fact.get("concept")

            if concept and concept not in distractors:
                distractors.append(concept)

            if len(distractors) == count:
                return distractors

        # -----------------------------------
        # Fallback 1
        # Same concept type (any topic)
        # -----------------------------------

        target_type = target_fact.get("concept_type")

        remaining = []

        for fact in facts:

            concept = fact.get("concept")

            if not concept:
                continue

            if concept == target_fact.get("concept"):
                continue

            if concept in distractors:
                continue

            if fact.get("concept_type") != target_type:
                continue

            remaining.append(concept)

        random.shuffle(remaining)

        for concept in remaining:

            distractors.append(concept)

            if len(distractors) == count:
                return distractors


        # -----------------------------------
        # Fallback 2
        # Same topic (any type)
        # -----------------------------------

        topic = target_fact.get("topic")

        remaining = []

        for fact in facts:

            concept = fact.get("concept")

            if not concept:
                continue

            if concept == target_fact.get("concept"):
                continue

            if concept in distractors:
                continue

            if fact.get("topic") != topic:
                continue

            remaining.append(concept)

        random.shuffle(remaining)

        for concept in remaining:

            distractors.append(concept)

            if len(distractors) == count:
                return distractors


        # -----------------------------------
        # Fallback 3
        # Any remaining concept
        # -----------------------------------

        remaining = []

        for fact in facts:

            concept = fact.get("concept")

            if not concept:
                continue

            if concept == target_fact.get("concept"):
                continue

            if concept in distractors:
                continue

            remaining.append(concept)

        random.shuffle(remaining)

        for concept in remaining:

            distractors.append(concept)

            if len(distractors) == count:
                return distractors

        return distractors