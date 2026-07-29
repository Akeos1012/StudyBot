from app.quiz.question_validator import is_valid_question

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
