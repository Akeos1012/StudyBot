# test_quick.py
"""Quick smoke test for the quiz system."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.rag.fact_cache import FactCache
from app.quiz.quiz_generator import QuizGenerator


def main():
    print("🚀 Quick Quiz Test")
    print("=" * 40)

    # Load cache
    cache = FactCache()
    cache.load()
    print(f"✅ Cache loaded")

    # Test with Algorithms
    topic = "Algorithms"
    facts = cache.get_facts(topic)
    print(f"✅ Found {len(facts)} facts for '{topic}'")

    if facts:
        # Generate questions
        gen = QuizGenerator()
        questions = gen.build_quiz(facts, count=3)

        print(f"✅ Generated {len(questions)} questions\n")

        for i, q in enumerate(questions, 1):
            print(f"Q{i}: {q['question']}")
            print(f"  Options: {q['options']}")
            print(f"  Correct: {q['correct_letter']} ({q['correct_answer']})")
            print(f"  Type: {q.get('question_type', 'unknown')}")
            print()

    # Test with Cloud
    topic = "Cloud"
    facts = cache.get_facts(topic)
    print(f"✅ Found {len(facts)} facts for '{topic}'")

    if facts:
        questions = gen.build_quiz(facts, count=2)
        print(f"✅ Generated {len(questions)} questions\n")

        for i, q in enumerate(questions, 1):
            print(f"Q{i}: {q['question']}")
            print(f"  Options: {q['options']}")
            print(f"  Correct: {q['correct_letter']} ({q['correct_answer']})")
            print()


if __name__ == "__main__":
    main()