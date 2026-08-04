import pytest
from unittest.mock import MagicMock
from app.tutor.answer_builder import AnswerBuilder
from app.models.retrieved_context import RetrievedContext
from app.models.tutor_schema import TutorIntent

@pytest.fixture
def mock_llm():
    return MagicMock()

@pytest.fixture
def builder(mock_llm):
    return AnswerBuilder(llm_client=mock_llm)

@pytest.fixture
def context():
    return RetrievedContext(
        found=True,
        facts=[{"fact_id": "f1", "definition": "Normalization reduces redundancy.", "concept": "Normalization", "topic": "DB", "source": "s"}],
        concepts=["Normalization"],
        topics=["DB"],
        sources=["s"],
        supporting_facts=["Normalization reduces redundancy."]
    )

def test_explain_intent(builder, mock_llm, context):
    mock_llm.generate_with_system.return_value = "Normalization reduces data redundancy."
    answer = builder.build(context, TutorIntent.EXPLAIN)
    
    assert answer == "Normalization reduces data redundancy."
    mock_llm.generate_with_system.assert_called_once()
    # Check context injection in system prompt
    args, kwargs = mock_llm.generate_with_system.call_args
    assert "Normalization reduces redundancy." in args[0]

def test_compare_intent(builder, mock_llm, context):
    mock_llm.generate_with_system.return_value = "| Concept | Description |\n|---|---|\n| RAM | Volatile |\n| ROM | Non-volatile |"
    answer = builder.build(context, TutorIntent.COMPARE)
    
    assert "| Concept | Description |" in answer
    assert "RAM" in answer
    assert "ROM" in answer
    
    args, kwargs = mock_llm.generate_with_system.call_args
    user_prompt = args[1]
    assert "Compare" in user_prompt
    assert "table" in user_prompt
    assert "4 rows" in user_prompt

def test_empty_context_raises(builder, mock_llm):
    empty_context = RetrievedContext(
        found=False, facts=[], concepts=[], topics=[], sources=[], supporting_facts=[]
    )
    with pytest.raises(ValueError):
        builder.build(empty_context, TutorIntent.EXPLAIN)
    mock_llm.generate_with_system.assert_not_called()

def test_grounding_protection(builder, mock_llm, context):
    # This test verifies that context is passed to the LLM. 
    # The grounding enforcement happens via the system prompt injection.
    builder.build(context, TutorIntent.EXPLAIN)
    
    args, kwargs = mock_llm.generate_with_system.call_args
    system_prompt = args[0]
    assert "<context>" in system_prompt
    assert "Normalization reduces redundancy." in system_prompt
