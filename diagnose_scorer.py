import json
from app.quiz.generation.question_scorer import QuestionScorer

scorer = QuestionScorer()

fixtures = {
    "Poor readability": {
        "question": "Regarding the intricate complexities inherent in modern cloud infrastructure systems, what is the specific technical term used to describe the primary function of Object Storage in cloud computing, considering all its various attributes?" * 5,
        "options": [
            "A) Object storage",
            "B) File storage",
            "C) Block storage",
            "D) Network storage"
        ],
        "correct": "A",
        "explanation": "Object storage is correct because it stores data as objects." * 10,
        "supporting_fact": "Object storage stores data as objects.",
    },
    "Bad distractors": {
        "question": "What is Object Storage?",
        "options": [
            "A) Object storage",
            "B) File storage",
            "C) File storage",
            "D) File storage"
        ],
        "correct": "A",
        "explanation": "Object storage stores data as objects.",
        "supporting_fact": "Object storage stores data as objects.",
    },
    "Semantic inconsistency": {
        "question": "What is the fastest way to travel to Mars?",
        "options": [
            "A) Object storage",
            "B) File storage",
            "C) Block storage",
            "D) Network storage"
        ],
        "correct": "A",
        "explanation": "Object storage stores data as objects.",
        "supporting_fact": "Object storage stores data as objects.",
    },
    "Unsupported explanation": {
        "question": "What is Object Storage?",
        "options": [
            "A) Object storage",
            "B) File storage",
            "C) Block storage",
            "D) Network storage"
        ],
        "correct": "A",
        "explanation": "It is made of cheese.",
        "supporting_fact": "Object storage stores data as objects.",
    }
}

for name, fixture in fixtures.items():
    total, scores, issues = scorer.score_question(fixture)
    print(f"--- {name} ---")
    print(f"Total: {total}")
    print(f"Scores: {json.dumps(scores, indent=2)}")
    print(f"Issues: {json.dumps(issues, indent=2)}")
    print("\n")
