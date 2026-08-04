import pytest
from unittest.mock import MagicMock
from app.rag.retriever import Retriever
from app.models.tutor_schema import NormalizedQuery

@pytest.fixture
def mock_fact_cache():
    cache = MagicMock()
    cache.get_topics.return_value = ["Database"]
    cache.get_facts.return_value = [
        {
            "concept": "Normalization",
            "definition": "Database normalization reduces redundancy",
            "topic": "Database",
            "source": "database/normalization.md",
            "fact_id": "f1",
            "weight": 5
        },
        {
            "concept": "Indexing",
            "definition": "Indexing improves query performance",
            "topic": "Database",
            "source": "database/indexing.md",
            "fact_id": "f2",
            "weight": 3
        }
    ]
    return cache

@pytest.fixture
def retriever(mock_fact_cache):
    return Retriever(fact_cache=mock_fact_cache)

def test_exact_concept_match(retriever):
    query = NormalizedQuery(
        original_question="Explain database normalization",
        normalized_text="normalization",
        keywords=["normalization"],
        extracted_concepts=["Normalization"]
    )
    result = retriever.search(query)
    
    assert result.found is True
    assert len(result.facts) >= 1
    assert result.facts[0]["concept"] == "Normalization"
    assert "database/normalization.md" in result.sources

def test_keyword_match(retriever):
    query = NormalizedQuery(
        original_question="How do tables reduce redundancy?",
        normalized_text="tables redundancy",
        keywords=["tables", "redundancy"],
        extracted_concepts=[]
    )
    result = retriever.search(query)
    
    assert result.found is True
    # Normalization fact should be found due to keyword match
    assert any(f["concept"] == "Normalization" for f in result.facts)

def test_unknown_topic(retriever):
    query = NormalizedQuery(
        original_question="What is quantum computing?",
        normalized_text="quantum computing",
        keywords=["quantum", "computing"],
        extracted_concepts=[]
    )
    result = retriever.search(query)
    
    assert result.found is False
    assert result.facts == []

def test_source_traceability(retriever):
    query = NormalizedQuery(
        original_question="Explain database normalization",
        normalized_text="normalization",
        keywords=["normalization"],
        extracted_concepts=["Normalization"]
    )
    result = retriever.search(query)
    
    fact = result.facts[0]
    assert "fact_id" in fact
    assert "source" in fact
    assert fact["source"] == "database/normalization.md"
    assert "database/normalization.md" in result.sources

def test_result_limit(retriever):
    # Setup cache with 12 facts
    retriever.fact_cache.get_facts.return_value = [{"concept": f"c{i}", "definition": "d", "topic": "Database", "source": "s", "fact_id": f"f{i}"} for i in range(12)]
    
    query = NormalizedQuery(
        original_question="Database",
        normalized_text="database",
        keywords=["database"],
        extracted_concepts=[]
    )
    result = retriever.search(query)
    
    assert len(result.facts) <= 10
