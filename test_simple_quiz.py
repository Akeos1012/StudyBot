from app.fact_cache import FactCache
from app.question_builder import QuestionBuilder

cache = FactCache()
cache.load()
builder = QuestionBuilder()
facts = cache.get_facts('Algorithms')
qs = builder.build_quiz(facts, 3)

print(f'Generated {len(qs)} questions')
for i, q in enumerate(qs, 1):
    print(f'\\nQ{i}: {q["question"]}')
    print(f'  Options: {q["options"]}')
    print(f'  Correct: {q["correct_answer"]}')
    print(f'  Type: {q.get("concept_type", "unknown")}')
    print(f'  Score: {builder.score_question_quality(q)["overall"]:.2f}')
