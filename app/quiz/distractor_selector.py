from typing import List, Dict, Any
import random


class DistractorSelector:

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

            # remove same answer
            if concept == target_concept:
                continue

            # same ontology type only
            if fact.get("concept_type") != target_type:
                continue

            candidates.append(fact)

        return candidates


    def select_distractors(
        self,
        facts: List[Dict[str, Any]],
        target_fact: Dict[str, Any],
        count: int = 3
    ) -> List[str]:

        compatible = self.get_compatible_facts(
            facts,
            target_fact
        )

        random.shuffle(compatible)

        distractors = []

        for fact in compatible:

            concept = fact.get("concept")

            if concept and concept not in distractors:
                distractors.append(concept)

            if len(distractors) == count:
                break

        return distractors