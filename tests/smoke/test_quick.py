from app.rag.fact_cache import FactCache
from app.quiz.quiz_generator import QuizGenerator


def test_quick_quiz_pipeline():
    cache = FactCache()
    cache.load()

    gen = QuizGenerator()

    # Test Algorithms
    algorithms_facts = cache.get_facts("Algorithms")

    assert isinstance(algorithms_facts, list)

    if algorithms_facts:
        result = gen.generate_questions(
            topic="Algorithms",
            supporting_facts=algorithms_facts,
            count=3
        )

        assert "questions" in result

    # Test Cloud
    cloud_facts = cache.get_facts("Cloud")

    assert isinstance(cloud_facts, list)

    if cloud_facts:
        result = gen.generate_questions(
            topic="Cloud",
            supporting_facts=cloud_facts,
            count=2
        )

        assert "questions" in result