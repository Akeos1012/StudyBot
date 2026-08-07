import pytest
from app.rag.fact_cache import FactCache
from app.rag.retriever import Retriever
from app.quiz.generation.quiz_generator import QuizGenerator
from app.quiz.validation.question_validator import is_valid_question

def test_pipeline_health():
    # 1. FactCache Health
    cache = FactCache()
    cache.load()
    removed_count = cache.validate_cache()
    assert removed_count == 0, "Cache validation failed: invalid facts found"
    topics = cache.get_topics()
    assert len(topics) > 0, "Cache contains no topics"
    
    # 2. Retrieval Health
    retriever = Retriever(cache)
    topic = topics[0]
    facts = retriever.retrieve(topic=topic, limit=1)
    assert len(facts) > 0, f"Retriever failed to retrieve facts for topic: {topic}"
    
    # 3. Quiz Generation Health
    from app.quiz.storage.question_cache import QuestionCache

    question_cache = QuestionCache()

    gen = QuizGenerator(
        cache=question_cache,
        fact_cache=cache
    )
    # Generate 1 question
    questions = gen.generate_questions(topic=topic, count=1, supporting_facts=facts)
    assert "questions" in questions, "QuizGenerator returned no questions"
    assert len(questions["questions"]) > 0, "Generated question list is empty"
    
    # 4. Validation Health
    question = questions["questions"][0]
    assert is_valid_question(question), "Generated question failed validation"
    
    print(f"\n✅ Pipeline health check passed for topic: {topic}")
