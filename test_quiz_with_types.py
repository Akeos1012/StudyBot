# test_quiz_with_types.py
from app.fact_cache import FactCache
from app.question_builder import QuestionBuilder
from collections import Counter

def main():
    cache = FactCache()
    cache.load()
    
    builder = QuestionBuilder()
    
    topics = ['Algorithms', 'AI']
    
    for topic in topics:
        facts = cache.get_facts(topic)
        if not facts:
            print(f"❌ No facts found for {topic}")
            continue
            
        print(f"\n📚 {topic}: {len(facts)} facts")
        
        # Show type distribution
        types = Counter(f.get('concept_type', 'unknown') for f in facts)
        print(f"  Types: {dict(types)}")
        
        questions = builder.build_quiz(facts, count=3)
        
        print(f"\n📝 Generated {len(questions)} questions for {topic}")
        
        for i, q in enumerate(questions, 1):
            print(f"\nQ{i}: {q['question']}")
            for opt in q['options']:
                print(f"  {opt}")
            print(f"  ✅ Correct: {q['correct_letter']} ({q['correct_answer']})")
            print(f"  📊 Type: {q.get('concept_type', 'unknown')}")
            print(f"  📝 Explanation: {q['explanation'][:100]}...")

if __name__ == "__main__":
    main()
