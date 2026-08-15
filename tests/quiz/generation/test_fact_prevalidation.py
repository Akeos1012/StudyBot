import pytest
from app.quiz.validation.fact_validator import FactValidator

@pytest.fixture
def validator():
    return FactValidator()

def test_fact_validator(validator):
    # Valid fact
    fact1 = {"concept": "Deep Learning", "supporting_fact": "Deep Learning is AI"}
    assert validator.validate(fact1).valid is True
    
    # Missing concept
    fact2 = {"concept": "", "supporting_fact": "Deep Learning is AI"}
    assert validator.validate(fact2).valid is False
    assert validator.validate(fact2).code == "missing_concept"
    
    # Missing supporting fact
    fact3 = {"concept": "Deep Learning", "supporting_fact": ""}
    assert validator.validate(fact3).valid is False
    assert validator.validate(fact3).code == "missing_definition"
    
    # Grounding mismatch (concept not in definition)
    fact4 = {"concept": "Deep Learning", "supporting_fact": "is AI"}
    assert validator.validate(fact4).valid is False
    assert validator.validate(fact4).code == "grounding_failure"
