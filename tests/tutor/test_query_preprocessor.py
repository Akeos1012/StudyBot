import pytest
from app.tutor.query_preprocessor import QueryPreprocessor

@pytest.fixture
def preprocessor():
    return QueryPreprocessor(known_concepts=["RAM", "ROM", "SQL", "Cloud Storage"])

def test_basic_normalization(preprocessor):
    result = preprocessor.preprocess("What is Cloud Storage?")
    assert "cloud" in result.keywords
    assert "storage" in result.keywords

def test_informal_query(preprocessor):
    result = preprocessor.preprocess("whats the diff between ram and rom")
    assert "ram" in result.keywords
    assert "rom" in result.keywords
    assert "difference" in result.keywords

def test_technical_phrase_preservation(preprocessor):
    result = preprocessor.preprocess("Explain database normalization")
    assert "database" in result.keywords
    assert "normalization" in result.keywords

def test_noise_removal(preprocessor):
    result = preprocessor.preprocess("Can you please explain what is SQL?")
    assert "sql" in result.keywords
    assert "can" not in result.keywords
    assert "please" not in result.keywords
    assert "explain" not in result.keywords
    assert "what" not in result.keywords
    assert "is" not in result.keywords

def test_empty_input(preprocessor):
    result = preprocessor.preprocess("")
    assert result.original_question == ""
    assert result.keywords == []

def test_concept_extraction(preprocessor):
    result = preprocessor.preprocess("How to use RAM?")
    assert "RAM" in result.extracted_concepts
