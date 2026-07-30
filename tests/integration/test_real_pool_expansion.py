import pytest
import json
import os
from unittest.mock import MagicMock, patch
from pathlib import Path
from app.services.quiz_service import QuizService
from app.quiz.pool_manager import PoolManager
from app.quiz.question_cache import QuestionCache
from app.quiz.quiz_generator import QuizGenerator
from app.rag.retriever import Retriever
from app.rag.fact_cache import FactCache
from app.rag.metadata_loader import MetadataLoader
from app.monitoring.pool_metrics import PoolMetrics

# Mock deterministic LLM response that passes validators
MOCK_LLM_RESPONSE = json.dumps({
    "questions": [
        {
            "question": "What is the foundational concept of Cloud computing?",
            "options": ["A) Remote storage", "B) Physical server", "C) Local disk", "D) USB drive"],
            "correct": "A",
            "type": "multiple_choice",
            "difficulty": "medium",
            "concept": "Cloud computing",
            "supporting_fact": "Cloud computing provides computing resources over the internet."
        }
    ]
})

@pytest.fixture
def temp_cache(tmp_path):
    cache_file = tmp_path / "test_cache.json"
    cache = QuestionCache(cache_file=str(cache_file))
    return cache

@pytest.fixture
def mocked_llm():
    with patch("app.quiz.llm_client.LLMClient.generate", return_value=MOCK_LLM_RESPONSE):
        yield

@pytest.fixture
def pipeline_setup(temp_cache, mocked_llm):
    # Setup FactCache and Retriever
    fact_cache = FactCache()
    # Adding sample data to fact cache
    fact_cache.facts = {
        "Cloud": [
            {"concept": "Cloud computing", "supporting_fact": "Cloud computing provides computing resources over the internet.", "difficulty_hint": "medium", "weight": 1.0},
            {"concept": "Virtual machines", "supporting_fact": "Virtual machines create virtualized computing environments.", "difficulty_hint": "hard", "weight": 1.0}
        ]
    }
    retriever = Retriever(fact_cache=fact_cache)
    
    # Setup Generator
    generator = QuizGenerator(cache=temp_cache, fact_cache=fact_cache)
    
    # Setup PoolManager
    pool_metrics = MagicMock(spec=PoolMetrics)
    pool_manager = PoolManager(
        cache=temp_cache,
        generator=generator,
        retriever=retriever,
        pool_metrics=pool_metrics
    )
    
    # Setup QuizService
    service = QuizService(
        metadata_loader=MagicMock(spec=MetadataLoader),
        quiz_generator=generator,
        pool_manager=pool_manager
    )
    
    return service, pool_manager, temp_cache, generator

def test_empty_pool_real_expansion_flow(pipeline_setup):
    service, pool_manager, cache, generator = pipeline_setup
    topic = "Cloud"
    
    # Ensure cache is empty
    assert cache.get_pool_size(topic) == 0
    
    # Mock retriever to provide facts
    with patch.object(pool_manager.retriever, 'retrieve', return_value=[{"concept": "Cloud computing", "supporting_fact": "Cloud computing provides computing resources over the internet.", "difficulty_hint": "medium", "weight": 1.0, "fact_id": "f1", "source": "note1"}]), \
         patch.object(generator.fact_cache, 'get_facts', return_value=[{"concept": "Cloud computing", "supporting_fact": "Cloud computing provides computing resources over the internet.", "difficulty_hint": "medium", "weight": 1.0, "fact_id": "f1", "source": "note1"}]):
        # Action: Trigger generation which should trigger expansion
        # Using a patch for the generator that ensures it returns what's expected.
        # The PoolManager.expand_pool expects generator.generate_questions to return a dict with a "questions" key.
        with patch.object(generator, 'generate_questions', return_value={"questions": [{
            "question": "What is the foundational concept of Cloud computing?",
            "options": ["A) Cloud computing", "B) Physical server", "C) Local disk", "D) USB drive"],
            "correct": "A",
            "correct_text": "Cloud computing",
            "type": "multiple_choice",
            "difficulty": "medium",
            "concept": "Cloud computing",
            "supporting_fact": "Cloud computing provides computing resources over the internet.",
            "explanation": "Cloud computing provides resources over the internet.",
            "fact_id": "f1",
            "source_note": "note1"
        }]}):
            questions = service.get_or_generate_questions(topic, count=5)
            print("DEBUG: questions returned:", questions)
            
            # Verify
            assert len(questions) > 0
            assert cache.get_pool_size(topic) >= 1
            assert questions[0]["concept"] == "Cloud computing"

def test_metadata_imbalance_real_expansion_flow(pipeline_setup):
    service, pool_manager, cache, generator = pipeline_setup
    topic = "Cloud"
    
    # Preload with enough questions so cache.sample() returns a list, not None.
    # The PoolManager uses ["multiple_choice", "fill_blank"] and ["easy", "medium", "hard"]
    questions = []
    for i in range(2):
        questions.append({"question": f"Easy {i}?", "options": ["A) Easy", "B) Hard", "C) Medium", "D) Wrong"], "correct": "A", "correct_text": "Easy", "type": "multiple_choice", "difficulty": "easy", "concept": f"Easy {i}", "supporting_fact": "Easy fact content", "explanation": "Explanation for easy", "fact_id": f"fact_{i}_easy", "source_note": "note1"})
        questions.append({"question": f"Medium {i}?", "options": ["A) Easy", "B) Hard", "C) Medium", "D) Wrong"], "correct": "A", "correct_text": "Easy", "type": "multiple_choice", "difficulty": "medium", "concept": f"Medium {i}", "supporting_fact": "Medium fact content", "explanation": "Explanation for medium", "fact_id": f"fact_{i}_med", "source_note": "note1"})

    for q in questions:
        cache.add_to_pool(topic, "", q["difficulty"], "multiple_choice", [q])
    
    # Initial state check - missing hard questions
    distribution = pool_manager.analyze_distribution(topic)
    assert distribution["difficulty"].get("hard", 0) == 0
    
    # Trigger expansion (should detect imbalance)
    # Patch generator to avoid actual generation during this test
    with patch.object(generator, 'generate_questions', return_value={"questions": []}):
        service.get_or_generate_questions(topic, count=1)
    
    # Verify distribution triggered expansion. 
    # should_expand_pool returns "expand": True if reasons exist.
    assert pool_manager.should_expand_pool(topic)["expand"] is True

def test_expansion_failure_fallback_flow(pipeline_setup):
    service, pool_manager, cache, generator = pipeline_setup
    topic = "Cloud"
    
    # Force generation failure in the generator
    with patch.object(generator, 'generate_questions', side_effect=Exception("Generation Failed")):
        # Mocking fallback note loader to still return something so it doesn't just return [] due to no notes
        with patch.object(service, '_get_notes_for_topic', return_value=[{"path": "note1", "content_length": 100}]), \
             patch.object(service.metadata_loader, 'get_note_content', return_value="Cloud computing provides resources."):
            
            # Action: request questions
            questions = service.get_or_generate_questions(topic, count=1)
            
            # Verify: Should not crash, might return fallback or empty if no fallback generated
            assert isinstance(questions, list)
            # Should not have corrupted the cache (no invalid questions added)
            assert cache.get_pool_size(topic) == 0
