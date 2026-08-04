import pytest
from unittest.mock import MagicMock
from app.tutor.query_retriever import QueryRetriever
from app.models.tutor_schema import NormalizedQuery
from app.models.retrieved_context import RetrievedContext

@pytest.fixture
def mock_retriever():
    return MagicMock()

@pytest.fixture
def query_retriever(mock_retriever):
    return QueryRetriever(retriever=mock_retriever)

@pytest.fixture
def mock_query():
    return NormalizedQuery(
        original_question="Explain database normalization",
        normalized_text="normalization",
        keywords=["normalization"],
        extracted_concepts=["Normalization"]
    )

def test_successful_retrieval(query_retriever, mock_retriever, mock_query):
    # Mock search to return 2 facts
    mock_retriever.search.return_value = RetrievedContext(
        found=True,
        facts=[{"fact_id": "f1", "source": "s1", "definition": "d1", "concept": "c1", "topic": "t1"},
               {"fact_id": "f2", "source": "s2", "definition": "d2", "concept": "c2", "topic": "t2"}],
        concepts=["c1", "c2"],
        topics=["t1", "t2"],
        sources=["s1", "s2"],
        supporting_facts=["d1", "d2"]
    )
    
    result = query_retriever.retrieve(mock_query)
    
    assert result.found is True
    assert len(result.facts) == 2
    mock_retriever.search.assert_called_once_with(mock_query)

def test_unknown_topic(query_retriever, mock_retriever, mock_query):
    # Mock search to return found=False
    mock_retriever.search.return_value = RetrievedContext(
        found=False, facts=[], concepts=[], topics=[], sources=[], supporting_facts=[]
    )
    
    result = query_retriever.retrieve(mock_query)
    
    assert result.found is False
    assert result.facts == []
    mock_retriever.search.assert_called_once_with(mock_query)

def test_context_limit(query_retriever, mock_retriever, mock_query):
    # Mock search to return 10 facts
    facts = [{"fact_id": f"f{i}", "source": "s", "definition": "d", "concept": "c", "topic": "t"} for i in range(10)]
    mock_retriever.search.return_value = RetrievedContext(
        found=True,
        facts=facts,
        concepts=["c"],
        topics=["t"],
        sources=["s"],
        supporting_facts=["d"]
    )
    
    result = query_retriever.retrieve(mock_query)
    
    # Verify limit to 5
    assert len(result.facts) == 5
    mock_retriever.search.assert_called_once_with(mock_query)

def test_traceability_preservation(query_retriever, mock_retriever, mock_query):
    # Mock search to return 1 fact
    mock_retriever.search.return_value = RetrievedContext(
        found=True,
        facts=[{"fact_id": "f1", "source": "s1", "definition": "d1", "concept": "c1", "topic": "t1"}],
        concepts=["c1"],
        topics=["t1"],
        sources=["s1"],
        supporting_facts=["d1"]
    )
    
    result = query_retriever.retrieve(mock_query)
    
    fact = result.facts[0]
    assert "fact_id" in fact
    assert "source" in fact
    assert fact["source"] == "s1"
    assert "fact_id" in fact
    assert fact["fact_id"] == "f1"
