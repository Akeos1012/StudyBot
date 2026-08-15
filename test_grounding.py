from app.quiz.validation.question_grounding import validate_grounding

def test_grounding_validation():
    concept = "Deep Learning"
    
    # Case where concept name is PRESERVED (NEW BEHAVIOR)
    supporting_fact = "Deep Learning is a branch of machine learning."
    question = {
        "correct": "A",
        "options": ["A) Deep Learning", "B) Something else"]
    }
    
    result = validate_grounding(question, "", supporting_fact=supporting_fact)
    print(f"Result (concept preserved): {result}")
    
    # Still test concept present as baseline
    result2 = validate_grounding(question, "", supporting_fact=supporting_fact)
    print(f"Result (concept present): {result2}")

test_grounding_validation()
