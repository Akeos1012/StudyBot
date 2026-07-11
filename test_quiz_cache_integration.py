from app.quiz.quiz_generator import QuizGenerator
from app.quiz.question_cache import QuestionCache


context = """
Cloud computing provides computing resources over the internet.
Cloud storage allows users to store files remotely.
Virtual machines create virtualized computing environments.
Object storage stores data as objects instead of traditional files.
Cloud databases provide managed database services through cloud platforms.
"""

topic = "Cloud Computing"


# Generate question
generator = QuizGenerator()

result = generator.generate_questions(
    context,
    topic,
    count=1,
    supporting_facts=[
        "Cloud storage allows users to store files remotely"
    ]
)

questions = result.get("questions", [])

print("\nGenerated questions:")
print(len(questions))


if questions:

    cache = QuestionCache("test_cache.json")

    cache.add_to_pool(
        topic=topic,
        subtopic="",
        difficulty="medium",
        qtype="multiple",
        new_questions=questions
    )

    print("\nCache summary:")
    print(cache.get_pool_summary())

    print("\nRetrieved question:")
    print(cache.sample(topic, count=1))

else:
    print("No valid questions generated")