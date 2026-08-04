import pytest
from unittest.mock import MagicMock
from app.services.tutor_service import TutorService
from app.models.tutor_schema import TutorIntent, NormalizedQuery
from app.models.retrieved_context import RetrievedContext
from app.models.tutor_response import TutorResponse

@pytest.fixture
def mocks():
    return {
        "preprocessor": MagicMock(),
        "classifier": MagicMock(),
        "retriever": MagicMock(),
        "fallback": MagicMock(),
        "builder": MagicMock(),
        "linker": MagicMock()
    }

@pytest.fixture
def tutor_service(mocks):
    return TutorService(
        query_preprocessor=mocks["preprocessor"],
        intent_classifier=mocks["classifier"],
        query_retriever=mocks["retriever"],
        fallback_handler=mocks["fallback"],
        answer_builder=mocks["builder"],
        source_linker=mocks["linker"]
    )

def test_successful_pipeline(tutor_service, mocks):
    question = "Explain normalization"
    normalized = NormalizedQuery(original_question=question, normalized_text="normalization", keywords=["norm"], extracted_concepts=[])
    intent = TutorIntent.EXPLAIN
    context = RetrievedContext(found=True, facts=[{}], concepts=[], topics=[], sources=[], supporting_facts=[])
    answer = "Answer"
    response = TutorResponse(found=True, answer=answer, sources=[], related_concepts=[], intent="EXPLAIN")

    mocks["preprocessor"].preprocess.return_value = normalized
    mocks["classifier"].classify.return_value = intent
    mocks["retriever"].retrieve.return_value = context
    mocks["builder"].build.return_value = answer
    mocks["linker"].link.return_value = response

    result = tutor_service.ask(question)

    assert result.found is True
    assert result.answer == answer
    mocks["builder"].build.assert_called_once()
    mocks["linker"].link.assert_called_once()
    mocks["fallback"].create_response.assert_not_called()

def test_unknown_topic_fallback(tutor_service, mocks):
    question = "Quantum computing"
    normalized = NormalizedQuery(original_question=question, normalized_text="", keywords=[], extracted_concepts=[])
    context = RetrievedContext(found=False, facts=[], concepts=[], topics=[], sources=[], supporting_facts=[])
    fallback_response = TutorResponse(found=False, answer="Fallback", sources=[], related_concepts=[], intent="UNKNOWN")

    mocks["preprocessor"].preprocess.return_value = normalized
    mocks["retriever"].retrieve.return_value = context
    mocks["fallback"].create_response.return_value = fallback_response

    result = tutor_service.ask(question)

    assert result.found is False
    mocks["fallback"].create_response.assert_called_once()
    mocks["builder"].build.assert_not_called()

def test_llm_failure_safety(tutor_service, mocks):
    question = "Explain normalization"
    normalized = NormalizedQuery(original_question=question, normalized_text="", keywords=[], extracted_concepts=[])
    context = RetrievedContext(found=True, facts=[{}], concepts=[], topics=[], sources=[], supporting_facts=[])

    mocks["preprocessor"].preprocess.return_value = normalized
    mocks["retriever"].retrieve.return_value = context
    mocks["builder"].build.side_effect = Exception("LLM Error")

    result = tutor_service.ask(question)

    assert result.found is False
    assert "An error occurred" in result.answer

def test_empty_question(tutor_service, mocks):
    result = tutor_service.ask("")
    
    assert result.found is False
    mocks["preprocessor"].preprocess.assert_not_called()
