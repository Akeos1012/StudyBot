from app.quiz.quiz_generator import QuizGenerator
from app.quiz.question_cache import QuestionCache
from app.rag.fact_cache import FactCache


def main():
    print("=" * 60)
    print("Building Question Cache")
    print("=" * 60)

    # Load facts
    fact_cache = FactCache()
    fact_cache.load()

    # Services
    generator = QuizGenerator()
    question_cache = QuestionCache()

    topics = fact_cache.get_topics()

    print(f"\nFound {len(topics)} topics.\n")

    total_generated = 0

    for topic in topics:

        print("=" * 50)
        print(f"TOPIC: {topic}")

        facts = fact_cache.get_facts(topic)

        print(f"Facts: {len(facts)}")

        if not facts:
            continue

        context = "\n".join(
            fact.get("definition", "")
            for fact in facts
        )

        result = generator.generate_questions(
            context=context,
            topic=topic,
            count=5,
            supporting_facts=facts
        )

        questions = result.get("questions", [])

        print(f"Generated: {len(questions)}")

        if questions:

            question_cache.add_to_pool(
                topic=topic,
                subtopic="",
                difficulty="medium",
                qtype="multiple",
                new_questions=questions
            )

            total_generated += len(questions)

    print("\n" + "=" * 60)
    print("Finished")
    print(f"Total questions generated: {total_generated}")

    print("\nPool Summary:")
    print(question_cache.get_pool_summary())


if __name__ == "__main__":
    main()