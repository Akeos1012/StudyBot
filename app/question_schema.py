# question_schema.py
"""
Unified Question Schema Contract
All questions must follow this structure.
"""

from typing import List, Dict, Any, Optional

QUESTION_SCHEMA = {
    "required": ["question", "options", "correct", "explanation"],
    "optional": ["_is_fallback", "source_notes", "concept_type", "difficulty"],
    "types": {
        "question": str,
        "options": list,
        "correct": str,
        "explanation": str,
        "_is_fallback": bool,
        "source_notes": list,
        "concept_type": str,
        "difficulty": float
    }
}

def validate_question_schema(question: Dict[str, Any]) -> bool:
    """Validate a question against the schema."""
    for field in QUESTION_SCHEMA["required"]:
        if field not in question:
            print(f"⚠️ Missing required field: {field}")
            return False
        if not question[field]:
            print(f"⚠️ Empty field: {field}")
            return False
    
    if len(question.get("options", [])) != 4:
        print("⚠️ Must have exactly 4 options")
        return False
    
    if question.get("correct", "") not in ["A", "B", "C", "D"]:
        print(f"⚠️ Correct must be A-D, got: {question.get('correct')}")
        return False
    
    return True