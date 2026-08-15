import re
from app.rag.fact_cleaner import clean_definition

def test_clean_definition_behavior():
    concept = "Deep Learning"
    definition = "Deep Learning is a branch of machine learning."
    
    cleaned = clean_definition(concept, definition)
    print(f"Original: '{definition}'")
    print(f"Concept: '{concept}'")
    print(f"Cleaned: '{cleaned}'")
    
    # Test 2
    concept2 = "Computer Vision"
    definition2 = "Computer Vision enables computers to interpret images."
    cleaned2 = clean_definition(concept2, definition2)
    print(f"\nOriginal: '{definition2}'")
    print(f"Concept: '{concept2}'")
    print(f"Cleaned: '{cleaned2}'")

test_clean_definition_behavior()
