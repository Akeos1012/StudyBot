import pytest
from app.rag.fact_cache import FactCache
from app.quiz.storage.question_cache import QuestionCache
from app.quiz.validation.question_validator import is_valid_question

def test_cache_integrity():
    # 1. FactCache Health
    fc = FactCache()
    fc.load()
    removed_count = fc.validate_cache()
    assert removed_count == 0, f"FactCache integrity failed: {removed_count} invalid facts removed"
    
    topics = fc.get_topics()
    assert len(topics) > 0, "FactCache is empty"
    
    # 2. Fact Schema Check
    sample_topic = topics[0]
    sample_facts = fc.get_facts(sample_topic)
    assert len(sample_facts) > 0
    sample_fact = sample_facts[0]
    assert "concept" in sample_fact, f"Fact missing 'concept' field: {sample_fact}"
    
    # 3. QuestionCache Health
    qc = QuestionCache()
    # Sample a question to verify stored question integrity
    questions = qc.sample(topic=sample_topic, count=1)
    
    # If questions exist in cache, validate them
    if questions:
        for q in questions:
            assert is_valid_question(q), f"Cached question failed validation: {q}"
