
import pytest
from app.quiz.validation.question_grounding import question_equals_answer

def test_short_answer_leakage():
    # Example provided in prompt
    question = "Big O Notation is used to describe an algorithm's behavior when the amount of input data increases, by showing how fast or slow it grows. Which of the following best describes this behavior?"
    options = ["A) Big O Notation", "B) Linear Growth", "C) Constant Time", "D) Quadratic Time"]
    
    # Should be rejected because "big o notation" is in the question stem
    assert question_equals_answer(question, options) is True

def test_long_answer_leakage():
    # Long answer (over 20 chars) - should still be rejected
    question = "Which standard methodology is Database Normalization?"
    options = ["A) Database Normalization", "B) Data Archiving", "C) Data Replication", "D) Data Encryption"]

    # "database normalization" is in question
    assert question_equals_answer(question, options) is True

def test_legitimate_non_leakage():
    # Legitimate question - should pass
    question = "Which of the following is NOT a benefit of cloud computing?"
    options = ["A) Cost Savings", "B) Scalability", "C) Reliability", "D) Manual Hardware Maintenance"]
    
    assert question_equals_answer(question, options) is False

def test_case_normalization():
    # Case normalization check
    question = "big o notation is used..."
    options = ["A) Big O Notation", "B) Other", "C) Other", "D) Other"]
    
    assert question_equals_answer(question, options) is True
