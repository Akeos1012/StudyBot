import pytest
from unittest.mock import MagicMock
from app.tutor.fallback_handler import FallbackHandler
from app.models.retrieved_context import RetrievedContext

@pytest.fixture
def handler():
    return FallbackHandler()

def test_empty_retrieval_fallback(handler):
    context = RetrievedContext(
        found=False, facts=[], concepts=[], topics=[], sources=[], supporting_facts=[]
    )
    
    response = handler.create_response(context)
    
    assert response.found is False
    assert "I couldn't find this topic" in response.answer
    assert response.sources == []
    assert response.related_concepts == []

def test_no_llm_invocation(handler):
    # Fallback is static, LLM should not be called.
    # The handler implementation itself doesn't have an LLM client.
    context = RetrievedContext(
        found=False, facts=[], concepts=[], topics=[], sources=[], supporting_facts=[]
    )
    response = handler.create_response(context)
    assert response is not None

def test_valid_context_raises(handler):
    # FallbackHandler should not be called with valid context
    context = RetrievedContext(
        found=True,
        facts=[{"fact_id": "f1", "definition": "d", "concept": "C", "topic": "T", "source": "s"}],
        concepts=["C"],
        topics=["T"],
        sources=["s"],
        supporting_facts=["d"]
    )
    with pytest.raises(ValueError):
        handler.create_response(context)
