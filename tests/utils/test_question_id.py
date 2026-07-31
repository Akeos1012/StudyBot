import pytest
from app.utils.question_id import generate_question_id

def test_deterministic_id():
    text = "What is the capital of France?"
    id1 = generate_question_id(text)
    id2 = generate_question_id(text)
    assert id1 == id2

def test_different_id_for_different_text():
    text1 = "What is the capital of France?"
    text2 = "What is the capital of Germany?"
    id1 = generate_question_id(text1)
    id2 = generate_question_id(text2)
    assert id1 != id2
