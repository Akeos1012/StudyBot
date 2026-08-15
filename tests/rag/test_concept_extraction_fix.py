
import pytest
from app.rag.fact_extractor import FactExtractor
from app.rag.fact_extractor import ConceptValidator

@pytest.fixture
def extractor():
    return FactExtractor()

def test_reject_adverb_commonly(extractor):
    text = "Commonly uses Deep Learning models like neural networks"
    concept = extractor.semantic_extractor.extract(text)
    assert concept is None

def test_reject_adverb_usually(extractor):
    text = "Usually performs classification tasks."
    concept = extractor.semantic_extractor.extract(text)
    assert concept is None

def test_reject_adverb_generally(extractor):
    text = "Generally allows multiple layers of abstraction."
    concept = extractor.semantic_extractor.extract(text)
    assert concept is None

def test_reject_repeats_until_model(extractor):
    text = "Repeats until model improves"
    concept = extractor.semantic_extractor.extract(text)
    assert concept is None

def test_preserve_valid_concepts(extractor):
    valid_texts = [
        "Deep Learning is a subset of machine learning.",
        "AI Model refers to a trained system.",
        "Computer Vision enables computers to see.",
        "Data Augmentation involves creating modified data.",
        "Backpropagation is a learning algorithm.",
        "Machine Learning uses data to learn.",
        "Neural Networks are inspired by the brain."
    ]
    
    expected_concepts = [
        "Deep Learning",
        "AI Model",
        "Computer Vision",
        "Data Augmentation",
        "Backpropagation",
        "Machine Learning",
        "Neural Networks"
    ]
    
    for text, expected in zip(valid_texts, expected_concepts):
        concept = extractor.semantic_extractor.extract(text)
        assert concept == expected

def test_reject_verb_phrase_starts(extractor):
    text = "Improves model performance by using more data."
    concept = extractor.semantic_extractor.extract(text)
    assert concept is None

def test_reject_fragment_markers_anywhere(extractor):
    # This might be tricky to trigger via extract regex, but we can test the structure validator directly
    assert extractor.semantic_extractor._has_valid_concept_structure("Model Because Error") is False
    assert extractor.semantic_extractor._has_valid_concept_structure("Learning Since Yesterday") is False
    assert extractor.semantic_extractor._has_valid_concept_structure("Process While Running") is False
