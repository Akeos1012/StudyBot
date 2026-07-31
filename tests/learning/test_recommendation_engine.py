import pytest
from app.learning.recommendation_engine import RecommendationEngine

@pytest.fixture
def engine():
    return RecommendationEngine()

def test_weak_concept_priority(engine):
    questions = [
        {"id": "1", "concept": "recursion"},
        {"id": "2", "concept": "arrays"}
    ]
    weak_concepts = ["recursion"]
    
    ranked = engine.rank_questions(questions, weak_concepts, [])
    
    # recursion (weak) score +2, arrays (neutral) score 0. 
    # Order should be recursion, arrays
    assert ranked[0]["id"] == "1"
    assert ranked[1]["id"] == "2"

def test_strong_concept_deprioritization(engine):
    questions = [
        {"id": "1", "concept": "arrays"},
        {"id": "2", "concept": "graphs"}
    ]
    strong_concepts = ["arrays"]
    
    ranked = engine.rank_questions(questions, [], strong_concepts)
    
    # arrays (strong) score -1, graphs (neutral) score 0.
    # Order should be graphs, arrays
    assert ranked[0]["id"] == "2"
    assert ranked[1]["id"] == "1"

def test_neutral_concepts_preserve_order(engine):
    questions = [
        {"id": "1", "concept": "graphs"},
        {"id": "2", "concept": "trees"}
    ]
    # Neutral: both score 0. Order should be preserved.
    ranked = engine.rank_questions(questions, [], [])
    
    assert ranked[0]["id"] == "1"
    assert ranked[1]["id"] == "2"
