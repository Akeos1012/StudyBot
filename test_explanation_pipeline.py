from app.quiz_generator import (
    QuizGenerator,
    build_consistent_explanation,
    explanation_contradicts_answer,
    validate_semantic,
)


def test_validation_rejects_contradictory_explanation():
    question = {
        "question": "Which layer of cloud computing defines how data storage and database services are delivered?",
        "options": [
            "A) Core Storage Layer",
            "B) Core Service Layer",
            "C) Core Infrastructure Layer",
            "D) Core Performance & Architecture Layer",
        ],
        "correct": "B",
        "explanation": "The Core Storage Layer is responsible for defining how data is physically stored in fixed-size blocks over the internet.",
    }

    assert validate_semantic(question) is False


def test_build_consistent_explanation_passes_validation():
    question = {
        "question": "Which layer of cloud computing defines how data storage and database services are delivered?",
        "options": [
            "A) Core Storage Layer",
            "B) Core Service Layer",
            "C) Core Infrastructure Layer",
            "D) Core Performance & Architecture Layer",
        ],
        "correct": "B",
    }

    question["explanation"] = build_consistent_explanation(
        question_text=question["question"],
        options=question["options"],
        correct_letter=question["correct"],
        correct_text="Core Service Layer",
        context="The service layer defines how data storage and database services are delivered over the internet.",
        facts=[],
    )

    assert validate_semantic(question) is True


def test_fallback_question_uses_consistent_explanation():
    generator = QuizGenerator()
    question = generator._generate_fallback_question(
        "Cloud storage provides scalable storage and processing services over the internet.",
        "Cloud Computing",
    )

    assert question is not None
    assert "explanation" in question
    assert not explanation_contradicts_answer(question)


if __name__ == "__main__":
    test_validation_rejects_contradictory_explanation()
    test_build_consistent_explanation_passes_validation()
    test_fallback_question_uses_consistent_explanation()
    print("Explanation pipeline tests passed")
