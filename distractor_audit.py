from app.quiz.generation.quiz_generator import QuizGenerator
import json

gen = QuizGenerator()
facts = gen.fact_cache.get_facts("AI")

# Generate 20 questions
result = gen.generate_questions(topic="AI", count=20, supporting_facts=facts)

# Print for audit
for i, q in enumerate(result['questions']):
    print(f"--- Q{i+1} ---")
    print(f"Question: {q.get('question')}")
    print(f"Correct Answer: {q.get('correct_text')}")
    print(f"Options: {q.get('options')}")
    print(f"Explanation: {q.get('explanation')}")
