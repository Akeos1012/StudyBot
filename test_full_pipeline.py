# test_full_pipeline.py
"""Test the full quiz generation pipeline."""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.rag.metadata_loader import MetadataLoader
from app.rag.fact_extractor import FactExtractor
from app.rag.fact_cache import FactCache
from app.quiz.quiz_generator import QuizGenerator
from app.services.quiz_service import QuizService


def test_full_pipeline():
    """Test the complete pipeline from notes to questions."""
    print("=" * 60)
    print("🧪 Testing Full Quiz Generation Pipeline")
    print("=" * 60)

    # Step 1: Load metadata
    print("\n📂 Step 1: Loading metadata...")
    loader = MetadataLoader("sample_notes")
    metadata = loader.load_metadata()
    print(f"  ✅ Loaded {len(metadata)} notes")

    # Step 2: Extract facts for a topic
    print("\n📝 Step 2: Extracting facts...")
    topic = "Cloud"
    extractor = FactExtractor()
    notes = loader.get_notes_by_topic(topic)
    print(f"  📚 Found {len(notes)} notes for '{topic}'")

    all_facts = []
    for note in notes[:3]:  # Use first 3 notes
        content = loader.get_truncated_content(note["path"], 2000)
        facts = extractor.extract_facts(content, topic, source=note["path"])
        all_facts.extend(facts)
        print(f"    - {note['title']}: {len(facts)} facts")

    print(f"  ✅ Extracted {len(all_facts)} total facts")

    # Step 3: Load facts into cache
    print("\n💾 Step 3: Loading facts into cache...")
    cache = FactCache()
    cache.load()

    # Step 4: Generate questions
    print("\n🤖 Step 4: Generating questions...")
    generator = QuizGenerator()
    facts = cache.get_facts(topic)

    if facts:
        questions = generator.build_quiz(facts, count=3)
        print(f"  ✅ Generated {len(questions)} questions")

        # Show sample
        for i, q in enumerate(questions, 1):
            print(f"\n  Q{i}: {q['question']}")
            print(f"       Options: {q['options']}")
            print(f"       Correct: {q['correct_letter']} ({q['correct_answer']})")
            print(f"       Type: {q.get('question_type', 'unknown')}")
    else:
        print("  ❌ No facts found in cache")

    print("\n" + "=" * 60)
    print("✅ Test complete!")


def test_quiz_service():
    """Test the QuizService orchestration."""
    print("\n" + "=" * 60)
    print("🧪 Testing QuizService")
    print("=" * 60)

    from app.services.quiz_service import QuizService

    loader = MetadataLoader("sample_notes")
    loader.load_metadata()

    service = QuizService(loader)

    # Test question generation
    print("\n📝 Generating questions for 'Cloud'...")
    questions = service.get_or_generate_questions(
        topic="Cloud",
        count=3,
        fresh=True
    )

    print(f"  ✅ Generated {len(questions)} questions")

    for i, q in enumerate(questions, 1):
        print(f"\n  Q{i}: {q.get('question', '')[:80]}...")
        print(f"       Answer: {q.get('correct', '')}")

    # Test fill-blank
    print("\n📝 Generating fill-blank questions...")
    fill_blank = service.get_or_generate_questions(
        topic="Cloud",
        count=2,
        fresh=True,
        question_type="fillblank"
    )

    print(f"  ✅ Generated {len(fill_blank)} fill-blank questions")

    for i, q in enumerate(fill_blank, 1):
        print(f"\n  Q{i}: {q.get('question', '')[:80]}...")
        print(f"       Answer: {q.get('correct', '')}")


if __name__ == "__main__":
    test_full_pipeline()
    test_quiz_service()