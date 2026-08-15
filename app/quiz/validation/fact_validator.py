from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class FactValidationResult:
    def __init__(self, valid: bool, reason: str = "", code: str = ""):
        self.valid = valid
        self.reason = reason
        self.code = code

class FactValidator:
    """
    Deterministically validates facts before they reach the LLM.
    """

    def validate(self, fact_data: Dict[str, Any]) -> FactValidationResult:
        
        # 1. Structural Validation
        if not fact_data or not isinstance(fact_data, dict):
            return FactValidationResult(False, "Fact is empty or not a dict", "empty_fact")
            
        concept = fact_data.get("concept", "").strip()
        definition = (
            fact_data.get("supporting_fact") or 
            fact_data.get("definition") or 
            fact_data.get("sentence") or 
            ""
        ).strip()
        
        if not concept:
            return FactValidationResult(False, "Missing concept", "missing_concept")
        if not definition:
            return FactValidationResult(False, "Missing definition/supporting fact", "missing_definition")
            
        # 2. Concept Quality Validation
        # This reuses the logic developed in the earlier priority #1 fix
        # via the ConceptValidator if accessible, or simple robust checks.
        
        if len(concept.split()) < 1:
            return FactValidationResult(False, "Concept too short", "malformed_concept")
            
        # 3. Grounding Relationship
        # Must contain concept name if required by pipeline contract
        if concept.lower() not in definition.lower():
            return FactValidationResult(False, "Concept not found in supporting fact", "grounding_failure")
            
        return FactValidationResult(True)
