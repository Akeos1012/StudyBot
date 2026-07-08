# test_full_system.py
"""Test the full quiz generation system"""

from app.quiz_generator import QuizGenerator
from app.fact_cache import FactCache

def test_basic_generation():
    print("=" * 50)
    print("Testing Basic Quiz Generation")
    print("=" * 50)
    
    gen = QuizGenerator()
    result = gen.generate_questions('Database normalization reduces redundancy.', 'Database', 1)
    
    if result.get('questions'):
        q = result['questions'][0]
        print(f"✅ Success!")
        print(f"   Question: {q['question']}")
        print(f"   Options: {q['options']}")
        print(f"   Correct: {q['correct']}")
        print(f"   Quality Score: {q.get('_quality_score', 'N/A')}")
    else:
        print("❌ Failed to generate question")
    
    print()

def test_with_facts():
    print("=" * 50)
    print("Testing with Real Facts")
    print("=" * 50)
    
    cache = FactCache()
    cache.load()
    
    facts = cache.get_facts('Algorithms')
    if not facts:
        print("❌ No facts found for Algorithms")
        return
    
    print(f"✅ Loaded {len(facts)} facts from cache")
    
    # Create context from first few facts
    context = ' '.join([f.get('definition', '') for f in facts[:5]])
    print(f"📝 Context length: {len(context)} characters")
    
    gen = QuizGenerator()
    result = gen.generate_questions(context, 'Algorithms', 1)
    
    if result.get('questions'):
        q = result['questions'][0]
        print(f"✅ Question generated!")
        print(f"   Question: {q['question']}")
        print(f"   Options: {q['options']}")
        print(f"   Correct: {q['correct']}")
        print(f"   Quality Score: {q.get('_quality_score', 'N/A')}")
    else:
        print("❌ Failed to generate question")

if __name__ == "__main__":
    test_basic_generation()
    test_with_facts()
