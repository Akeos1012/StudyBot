from typing import List, Dict, Any


class DistractorSelector:

    def get_compatible_facts(
        self, facts: List[Dict[str, Any]], target_fact: Dict[str, Any]
    ):
        target_type = target_fact.get("concept_type")

        return [
            f
            for f in facts
            if f.get("concept") != target_fact.get("concept")
            and f.get("concept_type") == target_type
        ]

    def select_distractors(
        self, facts: List[Dict[str, Any]], target_fact: Dict[str, Any], count: int = 3
    ) -> List[str]:

        compatible = self.get_compatible_facts(facts, target_fact)

        return [f.get("concept") for f in compatible[:count] if f.get("concept")]
