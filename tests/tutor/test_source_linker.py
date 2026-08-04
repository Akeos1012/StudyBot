import pytest
from app.tutor.source_linker import SourceLinker
from app.models.retrieved_context import RetrievedContext

@pytest.fixture
def linker():
    return SourceLinker()

def test_valid_source_linking(linker):
    context = RetrievedContext(
        found=True,
        facts=[{"fact_id": "f1", "source": "notes/db.md", "definition": "d", "concept": "C", "topic": "T"}],
        concepts=["C"],
        topics=["T"],
        sources=["notes/db.md"],
        supporting_facts=["d"]
    )
    answer = "Normalized database reduces redundancy."
    
    response = linker.link(context, answer, "EXPLAIN")
    
    assert response.found is True
    assert response.sources == ["notes/db.md"]
    assert response.related_concepts == ["C"]

def test_missing_source_metadata(linker):
    # Fact exists but source_note/source is missing
    context = RetrievedContext(
        found=True,
        facts=[{"fact_id": "f1", "definition": "d", "concept": "C", "topic": "T"}], # 'source' missing
        concepts=["C"],
        topics=["T"],
        sources=[],
        supporting_facts=["d"]
    )
    answer = "No source here."
    
    response = linker.link(context, answer, "EXPLAIN")
    
    assert response.sources == []

def test_unknown_concept_ignored(linker):
    # Answer mentions something not in context
    context = RetrievedContext(
        found=True,
        facts=[{"fact_id": "f1", "source": "s1", "definition": "d", "concept": "C1", "topic": "T"}],
        concepts=["C1"],
        topics=["T"],
        sources=["s1"],
        supporting_facts=["d"]
    )
    answer = "Database normalization uses Quantum Computing."
    
    response = linker.link(context, answer, "EXPLAIN")
    
    # Should only return C1, not Quantum Computing
    assert response.related_concepts == ["C1"]

def test_related_concepts(linker):
    context = RetrievedContext(
        found=True,
        facts=[{"fact_id": "f1", "source": "s1", "definition": "d", "concept": "C1", "topic": "T"},
               {"fact_id": "f2", "source": "s2", "definition": "d", "concept": "C2", "topic": "T"}],
        concepts=["C1", "C2"],
        topics=["T"],
        sources=["s1", "s2"],
        supporting_facts=["d", "d"]
    )
    
    response = linker.link(context, "answer", "EXPLAIN")
    assert sorted(response.related_concepts) == ["C1", "C2"]

def test_empty_retrieval(linker):
    context = RetrievedContext(
        found=False,
        facts=[],
        concepts=[],
        topics=[],
        sources=[],
        supporting_facts=[]
    )
    
    response = linker.link(context, "Cannot answer", "EXPLAIN")
    
    assert response.found is False
    assert response.sources == []
    assert response.related_concepts == []
