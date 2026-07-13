from app.quiz.question_cache import QuestionCache


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


cache = QuestionCache(
    cache_file="test_question_cache.json"
)


cache.add_to_pool(
    topic="Cloud Computing",
    subtopic="Storage",
    difficulty="medium",
    qtype="multiple",
    new_questions=[question]
)


pool = cache.get_pool(
    topic="Cloud Computing",
    subtopic="Storage",
    difficulty="medium",
    qtype="multiple"
)


print("POOL SIZE:", len(pool))
print(pool[0]["question"])