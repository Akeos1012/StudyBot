import pytest
from app.tutor.intent_classifier import IntentClassifier
from app.models.tutor_schema import NormalizedQuery, TutorIntent

@pytest.fixture
def classifier():
    return IntentClassifier()

def test_compare(classifier):
    query = NormalizedQuery(original_question="RAM vs ROM", normalized_text="", keywords=[], extracted_concepts=[])
    assert classifier.classify(query) == TutorIntent.COMPARE

def test_example(classifier):
    query = NormalizedQuery(original_question="Give me an example of SQL joins", normalized_text="", keywords=[], extracted_concepts=[])
    assert classifier.classify(query) == TutorIntent.EXAMPLE

def test_simplify(classifier):
    query = NormalizedQuery(original_question="Explain this in simple terms", normalized_text="", keywords=[], extracted_concepts=[])
    assert classifier.classify(query) == TutorIntent.SIMPLIFY

def test_explain(classifier):
    query = NormalizedQuery(original_question="What is normalization?", normalized_text="", keywords=[], extracted_concepts=[])
    assert classifier.classify(query) == TutorIntent.EXPLAIN

def test_question(classifier):
    query = NormalizedQuery(original_question="Why does indexing improve performance?", normalized_text="", keywords=[], extracted_concepts=[])
    assert classifier.classify(query) == TutorIntent.QUESTION

def test_unknown(classifier):
    query = NormalizedQuery(original_question="hello", normalized_text="", keywords=[], extracted_concepts=[])
    assert classifier.classify(query) == TutorIntent.UNKNOWN

def test_conflict_resolution(classifier):
    # Should prioritize COMPARE
    query = NormalizedQuery(original_question="What is the difference between RAM and ROM?", normalized_text="", keywords=[], extracted_concepts=[])
    assert classifier.classify(query) == TutorIntent.COMPARE
