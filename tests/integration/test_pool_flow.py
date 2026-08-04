import pytest
from unittest.mock import MagicMock
from app.services.quiz_service import QuizService
from app.quiz.pool_manager import PoolManager
from app.quiz.question_cache import QuestionCache
from app.learning.mastery_service import MasteryService

@pytest.fixture
def integration_setup(tmp_path):
    # Real cache, mocked dependencies
    question_cache = QuestionCache(cache_file=str(tmp_path / "test_cache.json"))
    generator = MagicMock()
    generator.cache = question_cache # Important: link real cache
    retriever = MagicMock()
    mastery_service = MagicMock(spec=MasteryService)
    history_service = MagicMock()
    analytics_service = MagicMock()
    recommendation_engine = MagicMock()
    
    # PoolManager is mocked to allow assertion on methods
    pool_manager = MagicMock()
    
    # QuizService is real
    service = QuizService(
        metadata_loader=MagicMock(),
        quiz_generator=generator,
        pool_manager=pool_manager,
        mastery_service=mastery_service,
        history_service=history_service,
        analytics_service=analytics_service,
        recommendation_engine=recommendation_engine,
        quiz_session_service=MagicMock()
    )
    
    return service, pool_manager, question_cache, generator, retriever, history_service

def test_healthy_pool_flow(integration_setup):
    service, pool_manager, cache, generator, retriever, history_service = integration_setup
    pool_manager.should_expand_pool = MagicMock(return_value={"expand": False})
    
    # Inject cache.sample mock to verify call
    cache.sample = MagicMock(return_value=[{"question": "q1"}])
    
    # Execution
    service.get_or_generate_questions("Cloud", count=1)
    
    pool_manager.should_expand_pool.assert_called()
    assert not pool_manager.expand_pool.called
    assert cache.sample.called

def test_empty_pool_expansion_flow(integration_setup):
    service, pool_manager, cache, generator, retriever, history_service = integration_setup
    
    # Trigger expansion
    pool_manager.should_expand_pool = MagicMock(return_value={"expand": True})
    
    # Mock expansion action
    pool_manager.expand_pool = MagicMock(return_value=True)
    
    # Mock cache to return results *after* expansion
    cache.sample = MagicMock(return_value=[{"question": "q_new", "type": "multiple_choice"}])
    
    # Execution
    result = service.get_or_generate_questions("Cloud", count=1)
    
    # Verify
    pool_manager.expand_pool.assert_called()
    assert len(result) == 1

def test_expansion_failure_fallback(integration_setup):
    service, pool_manager, cache, generator, retriever, history_service = integration_setup
    
    # Force expand_pool to fail
    pool_manager.should_expand_pool = MagicMock(return_value={"expand": True})
    pool_manager.expand_pool = MagicMock(side_effect=Exception("Failure"))
    
    # Mock cache to empty to trigger fallback
    cache.sample = MagicMock(return_value=[])
    
    # Mock existing fallback generation
    generator.fact_cache.get_facts.return_value = [] # Force live extraction
    generator.generate_with_retry.return_value = {"question": "fallback", "type": "multiple_choice"}
    generator.generate_fill_blank.return_value = {"questions": []}
    
    # Mock metadata_loader for fallback
    service.metadata_loader.get_notes_by_topic.return_value = [{"path": "note1"}]
    service.metadata_loader.get_note_content.return_value = "content"
    
    # Mock FactExtractor and GroundingProcessor for fallback
    # They are created inside _extract_facts_from_notes, need to patch them.
    from unittest.mock import patch
    with patch('app.services.quiz_service.FactExtractor') as MockExtractor, \
         patch('app.services.quiz_service.GroundingProcessor') as MockGrounder:
        
        MockExtractor.return_value.extract_facts.return_value = [{"concept": "c1", "supporting_fact": "f1"}]
        MockGrounder.return_value.ground_all.return_value = [{"concept": "c1", "supporting_fact": "f1"}]
        
        # Execution should not crash
        result = service.get_or_generate_questions("Cloud", count=1)
        assert len(result) > 0
        assert result[0]["question"] == "fallback"

def test_metadata_imbalance_trigger(integration_setup):
    service, pool_manager, cache, generator, retriever, history_service = integration_setup
    
    # Mock imbalance
    pool_manager.should_expand_pool = MagicMock(return_value={"expand": True, "reasons": ["imbalance"]})
    generator.generate_questions.return_value = {"questions": [{"question": "q_imbalance"}]}
    retriever.retrieve.return_value = ["fact"]
    
    # Execution
    service.get_or_generate_questions("Cloud", count=1)
    
    pool_manager.expand_pool.assert_called()
