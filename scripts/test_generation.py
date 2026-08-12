import json
from app.quiz.generation.quiz_generator import QuizGenerator

gen = QuizGenerator()

facts = gen.fact_cache.get_facts("AI")
result = gen.generate_questions(topic="AI", count=5, supporting_facts=facts)

print(json.dumps(result, indent=2))
