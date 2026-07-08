import asyncio
from app.main import generate_quiz
from app.question_cache import QuestionCache
from app.quiz_generator import explanation_contradicts_answer

cache = QuestionCache()
cache.invalidate_topic_cache('Cloud Computing', '', 'medium', 'multiple')
response = asyncio.run(generate_quiz({'topic': 'Cloud Computing', 'count': 5, 'fresh': True}))
questions = response.get('questions', [])
print('returned_questions', len(questions))
bad = []
for i, q in enumerate(questions, 1):
    print(f'Q{i}: {q.get("question")}; correct={q.get("correct")}; explanation={q.get("explanation")}')
    if explanation_contradicts_answer(q):
        bad.append(i)
print('contradictions', bad)
print('pool_size', len(cache.get_pool('Cloud Computing', '', 'medium', 'multiple')))
