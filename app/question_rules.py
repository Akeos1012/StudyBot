# question_rules.py
"""
Comparison rules for concept types.
Uses schema.py as the source of truth.
"""

from typing import Dict, Any, Tuple, List, Optional
from .schema import ConceptType, can_compare_concepts, get_compatible_types

# ============ DEPRECATED: Keep for backward compatibility ============
# These are now defined in schema.py via ConceptType
# Keeping this here for reference but using schema.py's logic

# ============ COMPARISON RULES (Using schema.py) ============

def can_compare(fact1: Dict[str, Any], fact2: Dict[str, Any]) -> bool:
    """
    Check if two facts can be meaningfully compared.
    Uses schema.py's ConceptType.can_compare() as the source of truth.
    
    Args:
        fact1: First fact dict with 'concept_type' field
        fact2: Second fact dict with 'concept_type' field
    
    Returns:
        True if the facts can be compared, False otherwise
    """
    # Get concept types
    type1 = fact1.get('concept_type', 'concept')
    type2 = fact2.get('concept_type', 'concept')
    
    # Use schema's comparison logic
    return can_compare_concepts(type1, type2)


def get_compatible_facts(facts: List[Dict[str, Any]], fact: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get all facts that are compatible with the given fact.
    
    Args:
        facts: List of fact dicts
        fact: The fact to compare against
    
    Returns:
        List of compatible facts
    """
    compatible = []
    for other in facts:
        if other.get('concept') == fact.get('concept'):
            continue  # Skip the same fact
        if can_compare(fact, other):
            compatible.append(other)
    return compatible


def get_compatible_types_for_fact(fact: Dict[str, Any]) -> List[str]:
    """
    Get all concept types that are compatible with this fact's type.
    
    Args:
        fact: Fact dict with 'concept_type' field
    
    Returns:
        List of compatible type names
    """
    concept_type = fact.get('concept_type', 'concept')
    return get_compatible_types(concept_type)


def get_comparison_summary(facts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Get a summary of comparison capabilities for a set of facts.
    Useful for debugging and understanding your data.
    
    Args:
        facts: List of fact dicts
    
    Returns:
        Dict with comparison statistics
    """
    from collections import Counter
    
    # Count types
    type_counts = Counter()
    for f in facts:
        ctype = f.get('concept_type', 'concept')
        type_counts[ctype] += 1
    
    # Build compatibility matrix
    types = list(type_counts.keys())
    compatibility_matrix = {}
    
    for t1 in types:
        compatibility_matrix[t1] = {}
        for t2 in types:
            compatibility_matrix[t1][t2] = can_compare_concepts(t1, t2)
    
    return {
        'total_facts': len(facts),
        'type_counts': dict(type_counts),
        'compatibility_matrix': compatibility_matrix,
        'can_compare_any': any(
            can_compare_concepts(t1, t2) 
            for t1 in types 
            for t2 in types 
            if t1 != t2
        )
    }


# ============ LEGACY SUPPORT ============

# Keep the old COMPARISON_RULES for backward compatibility
# But mark as deprecated with a warning
COMPARISON_RULES = {
    "allowed_comparisons": [
        ("algorithm", "algorithm"),
        ("model", "model"),
        ("metric", "metric"),
        ("system", "system"),
        ("process", "process"),
    ],
    "disallowed_comparisons": [
        ("algorithm", "model"),
        ("model", "metric"),
        ("system", "algorithm"),
    ]
}


def can_compare_legacy(fact1, fact2):
    """
    Legacy comparison function using hardcoded rules.
    Deprecated: Use can_compare() instead, which uses schema.py.
    """
    if not hasattr(fact1, 'concept_type') or not hasattr(fact2, 'concept_type'):
        return False
    
    # Try to get concept_type as string
    type1 = fact1.concept_type if hasattr(fact1, 'concept_type') else fact1.get('concept_type', 'concept')
    type2 = fact2.concept_type if hasattr(fact2, 'concept_type') else fact2.get('concept_type', 'concept')
    
    pair = (type1, type2)
    return pair in COMPARISON_RULES["allowed_comparisons"]


# ============ FACTORY FUNCTIONS ============

def create_comparison_question(fact1: Dict[str, Any], fact2: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Create a comparison question from two facts.
    Only works if the facts can be compared.
    
    Args:
        fact1: First fact
        fact2: Second fact
    
    Returns:
        Question dict or None if not comparable
    """
    if not can_compare(fact1, fact2):
        return None
    
    concept1 = fact1.get('concept', 'Unknown')
    concept2 = fact2.get('concept', 'Unknown')
    definition1 = fact1.get('definition', '')
    definition2 = fact2.get('definition', '')
    
    # Generate a comparison question
    templates = [
        f"What is the main difference between {concept1} and {concept2}?",
        f"How does {concept1} differ from {concept2}?",
        f"Which statement best describes the relationship between {concept1} and {concept2}?",
        f"What distinguishes {concept1} from {concept2}?"
    ]
    
    import random
    question_text = random.choice(templates)
    
    return {
        'question': question_text,
        'correct_answer': concept1,
        'distractors': [concept2],
        'explanation': f"{concept1}: {definition1}\n\n{concept2}: {definition2}",
        'concept_type': fact1.get('concept_type', 'concept'),
        '_is_comparison': True
    }


# ============ TEST ============

if __name__ == "__main__":
    # Test with sample facts
    test_facts = [
        {'concept': 'Quick Sort', 'concept_type': 'algorithm'},
        {'concept': 'Merge Sort', 'concept_type': 'algorithm'},
        {'concept': 'Deep Learning', 'concept_type': 'model'},
        {'concept': 'Time Complexity', 'concept_type': 'metric'},
    ]
    
    print("=" * 50)
    print("Testing question_rules.py")
    print("=" * 50)
    
    # Test compatibility
    print("\n📊 Compatibility tests:")
    for i, f1 in enumerate(test_facts):
        for j, f2 in enumerate(test_facts):
            if i < j:
                result = can_compare(f1, f2)
                print(f"  {f1['concept']} ({f1['concept_type']}) vs {f2['concept']} ({f2['concept_type']}): {'✅' if result else '❌'}")
    
    # Test get_compatible_facts
    print("\n📚 Compatible facts for 'Quick Sort':")
    compatible = get_compatible_facts(test_facts, test_facts[0])
    for f in compatible:
        print(f"  - {f['concept']} ({f['concept_type']})")
    
    # Test summary
    print("\n📈 Summary:")
    summary = get_comparison_summary(test_facts)
    print(f"  Total facts: {summary['total_facts']}")
    print(f"  Type counts: {summary['type_counts']}")
    print(f"  Can compare any: {summary['can_compare_any']}")
    
    print("\n✅ All tests passed!")