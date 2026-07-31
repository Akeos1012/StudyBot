from app.quiz.question_validator import is_valid_question, has_grounded_explanation
from app.quiz.question_grounding import explanation_supported_by_fact

def test_is_valid_question():
    question = {
        "question": "Which type of cloud storage organizes data as individual objects?",
        "options": [
            "A) Object storage",
            "B) File storage",
            "C) Block storage",
            "D) Network storage"
        ],
        "correct": "A",
        "correct_text": "Object storage",
        "supporting_fact": "Object storage stores data as objects instead of traditional files",
        "explanation": "Object storage is correct because it stores data as objects.",
        "source_note": "cloud_notes.md",
        "fact_id": "fact_001"
    }

    assert is_valid_question(question) is True

def test_ungrounded_explanation_rejected():
    question = {
        "question": "What is Object Storage?",
        "options": [
            "A) Object storage",
            "B) File storage",
            "C) Block storage",
            "D) Network storage"
        ],
        "correct": "A",
        "correct_text": "Object storage",
        "supporting_fact": "Object storage stores data as objects.",
        "explanation": "Something unrelated to the fact.",
        "source_note": "cloud_notes.md",
        "fact_id": "fact_001"
    }

    assert has_grounded_explanation(question) is False

def test_grounding_false_negative_variation():
    fact = "A database stores and organizes data so applications can retrieve information efficiently."
    correct_text = "database"
    explanation = "The database keeps information in an organized structure, allowing programs to access stored data."
    # Coverage calculation (Tokens len > 3, excluding STOP_WORDS):
    # Fact tokens: database, stores, organizes, data, applications, retrieve, information, efficiently (8 total)
    # Explanation tokens: database, keeps, information, organized, structure, allowing, programs, access, stored, data (10 total)
    # Common: database, information, data (3 total)
    # Coverage: 3 / 8 = 0.375.
    # Current threshold: coverage >= 0.40 AND len(common) >= 3.
    # This test demonstrates that a valid explanation is rejected because of rigid coverage requirements.
    assert explanation_supported_by_fact(explanation, fact, correct_text) is True
