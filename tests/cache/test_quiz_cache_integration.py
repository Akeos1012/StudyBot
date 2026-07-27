"""
Integration test:
FactCache -> QuizGenerator -> DistractorSelector -> Question Validation

Uses real facts_cache.json.
"""
from app.rag.retriever import Retriever
from app.rag.fact_cache import FactCache
from app.quiz.quiz_generator import QuizGenerator


def main():

    print("=" * 60)
    print("QUIZ CACHE INTEGRATION TEST")
    print("=" * 60)

    print("\n[1] Loading fact cache...")

    fact_cache = FactCache()

    fact_cache.load()

    topics = fact_cache.get_topics()

    print(f"Available topics: {topics}")

    if not topics:
        raise RuntimeError(
            "No topics available in fact cache"
        )

    topic = topics[0]

    print(f"Using topic: {topic}")

    facts = fact_cache.get_facts(topic)

    print(f"Loaded facts: {len(facts)}")

    if not facts:
        raise RuntimeError(
            f"No facts found for topic: {topic}"
        )


    # 2. Validate schema
    print("\n[2] Checking fact schema...")

    missing_fields = []

    required = [
        "concept",
        "definition",
        "topic",
        "concept_type"
    ]

    for fact in facts:

        for field in required:
            if field not in fact:
                missing_fields.append(
                    {
                        "concept": fact.get("concept"),
                        "missing": field
                    }
                )


    if missing_fields:
        print("Missing fields:")
        for item in missing_fields:
            print(item)

        raise RuntimeError(
            "Fact schema validation failed"
        )

    print("All facts contain required fields")


    # 3. Initialize generator
    print("\n[3] Initializing QuizGenerator...")

    generator = QuizGenerator()
    generator.cache.clear()

    # Use the same validated cache instance
    generator.fact_cache = fact_cache
    generator.retriever = Retriever(fact_cache)


    # 4. Generate quiz
    print("\n[4] Generating question...")

    facts = fact_cache.get_facts(topic)

    result = generator.generate_questions(
        topic=topic,
        count=1,
        supporting_facts=facts
    )


    # 5. Validate output
    print("\n[5] Checking result...")

    questions = result.get(
        "questions",
        []
    )


    if not questions:

        raise RuntimeError(
            "No valid questions generated"
        )


    question = questions[0]


    print("\nSUCCESS")
    print("-" * 60)

    print("Question:")
    print(question["question"])

    print("\nOptions:")
    for option in question["options"]:
        print(option)

    print("\nCorrect:")
    print(question["correct"])

    print("\nExplanation:")
    print(question.get("explanation"))


if __name__ == "__main__":
    main()