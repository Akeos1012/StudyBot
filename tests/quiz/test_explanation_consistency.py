from app.quiz.quiz_generator import validate_semantic


def test_rejects_explanation_for_wrong_option():
    question = {
        "question": "Which layer of cloud computing defines how data storage and database services are delivered?",
        "options": [
            "A) Core Storage Layer",
            "B) Core Service Layer",
            "C) Core Infrastructure Layer",
            "D) Core Performance & Architecture Layer",
        ],
        "correct": "B",
        "explanation": "The Core Storage Layer is responsible for defining how data is physically stored in fixed-size blocks over the internet."
    }

    assert validate_semantic(question) is False


if __name__ == "__main__":
    test_rejects_explanation_for_wrong_option()
    print("Explanation consistency test passed")
