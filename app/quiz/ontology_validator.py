"""
Ontology Validator - Lightweight semantic validation layer.

This module provides semantic validation for concepts and question types.
It does NOT define ontology data (types, hierarchy, difficulty tables, etc.).
All ontology data is imported from app.models.fact_schema, which is the
single source of truth.

Responsibilities:
- Validate concept types
- Get compatible question types for a concept type
- Get question difficulty scores
- Compare concept types for compatibility

This module should remain small and focused on validation logic only.
"""

from typing import List, Optional
from .fact_schema import (
    ConceptType,
    can_compare_concepts,
    get_question_types_for_type,
    get_question_difficulty,
)

# ============================================================================
# MAIN VALIDATOR CLASS
# ============================================================================


class OntologyValidator:
    """
    Semantic validator for concepts and question types.

    All ontology data is sourced from fact_schema.py.
    This class only provides a convenience layer for validation.

    Usage:
        validator = OntologyValidator()
        if validator.validate_type("algorithm"):
            types = validator.get_compatible_question_types("algorithm")
            difficulty = validator.get_question_difficulty("algorithm", "definition")
    """

    def __init__(self):
        """Initialize the validator with ontology data from fact_schema."""
        # Cache valid types for fast lookup
        self._valid_types = [t.value for t in ConceptType]
        # Cache hierarchy for fast access
        self._hierarchy = ConceptType.get_hierarchy()

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def validate_type(self, type_name: str) -> bool:
        """
        Validate if a type name is a valid ConceptType.

        Args:
            type_name: The concept type name to validate

        Returns:
            True if the type is valid, False otherwise

        Example:
            >>> validator.validate_type("algorithm")
            True
            >>> validator.validate_type("invalid_type")
            False
        """
        if not type_name:
            return False
        return type_name in self._valid_types

    def get_compatible_question_types(self, concept_type: str) -> List[str]:
        """
        Get valid question types for a concept type.

        This is a convenience wrapper around get_question_types_for_type()
        from fact_schema.py.

        Args:
            concept_type: The concept type (e.g., "algorithm", "model")

        Returns:
            List of compatible question type names

        Example:
            >>> validator.get_compatible_question_types("algorithm")
            ['definition', 'comparison', 'application']
        """
        return get_question_types_for_type(concept_type)

    def get_question_difficulty(self, concept_type: str, question_type: str) -> float:
        """
        Get difficulty score for a question.

        This is a convenience wrapper around get_question_difficulty()
        from fact_schema.py.

        Args:
            concept_type: The concept type
            question_type: The question type

        Returns:
            Difficulty score between 0.0 and 1.0

        Example:
            >>> validator.get_question_difficulty("algorithm", "definition")
            0.3
        """
        return get_question_difficulty(concept_type, question_type)

    def can_compare(self, type_a: str, type_b: str) -> bool:
        """
        Check if two concept types can be meaningfully compared.

        This is a convenience wrapper around can_compare_concepts()
        from fact_schema.py.

        Args:
            type_a: First concept type
            type_b: Second concept type

        Returns:
            True if the types can be compared, False otherwise

        Example:
            >>> validator.can_compare("algorithm", "algorithm")
            True
            >>> validator.can_compare("algorithm", "model")
            False
        """
        return can_compare_concepts(type_a, type_b)

    def get_hierarchy(self) -> dict:
        """
        Get the full type hierarchy.

        This is a convenience wrapper around ConceptType.get_hierarchy()
        from fact_schema.py.

        Returns:
            The type hierarchy dictionary
        """
        return self._hierarchy

    def get_type_info(self, type_name: str) -> Optional[dict]:
        """
        Get detailed information about a concept type.

        Args:
            type_name: The concept type name

        Returns:
            Dictionary with type information, or None if type is invalid
        """
        if not self.validate_type(type_name):
            return None

        hierarchy = self.get_hierarchy()
        type_info = hierarchy.get(type_name, {})

        return {
            "name": type_name,
            "parent": type_info.get("parent"),
            "children": type_info.get("children", []),
            "level": type_info.get("level", 0),
            "compatible_question_types": self.get_compatible_question_types(type_name),
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


def validate_concept_type(type_name: str) -> bool:
    """
    Convenience function to validate a concept type.

    Args:
        type_name: The concept type name

    Returns:
        True if valid, False otherwise
    """
    validator = OntologyValidator()
    return validator.validate_type(type_name)


def get_compatible_question_types(type_name: str) -> List[str]:
    """
    Convenience function to get compatible question types.

    Args:
        type_name: The concept type name

    Returns:
        List of compatible question type names
    """
    validator = OntologyValidator()
    return validator.get_compatible_question_types(type_name)


def get_question_difficulty_score(concept_type: str, question_type: str) -> float:
    """
    Convenience function to get question difficulty.

    Args:
        concept_type: The concept type
        question_type: The question type

    Returns:
        Difficulty score between 0.0 and 1.0
    """
    validator = OntologyValidator()
    return validator.get_question_difficulty(concept_type, question_type)


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    validator = OntologyValidator()

    print("=== OntologyValidator Tests ===")

    # Test validate_type
    print(f"\nvalidate_type('algorithm'): {validator.validate_type('algorithm')}")
    print(f"validate_type('invalid'): {validator.validate_type('invalid')}")

    # Test get_compatible_question_types
    print(
        f"\nget_compatible_question_types('algorithm'): {validator.get_compatible_question_types('algorithm')}"
    )
    print(
        f"get_compatible_question_types('metric'): {validator.get_compatible_question_types('metric')}"
    )

    # Test get_question_difficulty
    print(
        f"\nget_question_difficulty('algorithm', 'definition'): {validator.get_question_difficulty('algorithm', 'definition')}"
    )
    print(
        f"get_question_difficulty('model', 'scenario'): {validator.get_question_difficulty('model', 'scenario')}"
    )

    # Test can_compare
    print(
        f"\ncan_compare('algorithm', 'algorithm'): {validator.can_compare('algorithm', 'algorithm')}"
    )
    print(
        f"can_compare('algorithm', 'model'): {validator.can_compare('algorithm', 'model')}"
    )

    # Test get_type_info
    print(f"\nget_type_info('algorithm'): {validator.get_type_info('algorithm')}")
