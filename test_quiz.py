from app.fact_cache import FactCache
from app.question_builder import QuestionBuilder

cache = FactCache()
cache.load()

builder = QuestionBuilder()

# Test with Algorithms
facts = cache.get_facts('Algorithms')
print(f"Algorithms: {len(facts)} facts")

questions = builder.build_quiz(facts, 3)
print(f"Generated {len(questions)} questions")
for i, q in enumerate(questions):
    print(f"Q{i+1}: {q['question']}")
    print(f"  Options: {q['options']}")
    print(f"  Correct: {q['correct_letter']} ({q['correct_answer']})")
    print()

# Test with AI
facts = cache.get_facts('AI')
print(f"AI: {len(facts)} facts")

questions = builder.build_quiz(facts, 3)
print(f"Generated {len(questions)} questions")
for i, q in enumerate(questions):
    print(f"Q{i+1}: {q['question']}")
    print(f"  Options: {q['options']}")
    print(f"  Correct: {q['correct_letter']} ({q['correct_answer']})")
    print()