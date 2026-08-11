import pytest
from app.quiz.generation.question_scorer import QuestionScorer, DEFAULT_WEIGHTS
from app.config import settings

# Benchmark threshold (not production threshold)
QUALITY_THRESHOLD = 0.80

@pytest.fixture
def scorer():
    return QuestionScorer()

def test_production_threshold_unchanged():
    # Verify current production threshold is 0.60
    assert settings.DEFAULT_MIN_SCORE == 0.60

def test_high_quality_question_score(scorer):
    question = {
        "question": "What is the primary function of Object Storage in cloud computing?",
        "options": [
            "A) Object storage",
            "B) File storage",
            "C) Block storage",
            "D) Network storage"
        ],
        "correct": "A",
        "explanation": "Object storage organizes data as individual objects, which allows for efficient retrieval in cloud environments.",
        "supporting_fact": "Object storage stores data as objects, enabling efficient retrieval and management in cloud environments.",
    }
    
    total, scores, issues = scorer.score_question(question)
    
    assert total >= QUALITY_THRESHOLD, (
        f"Expected high-quality question score >= {QUALITY_THRESHOLD}, "
        f"got {total}. Scores: {scores}, Issues: {issues}"
    )

def test_poorly_worded_question(scorer):
    # Violates readability: Extremely long question and explanation
    question = {
        "question": "Regarding the intricate complexities inherent in modern cloud infrastructure systems, what is the specific technical term used to describe the primary function of Object Storage in cloud computing, considering all its various attributes?" * 5,
        "options": [
            "A) Object storage",
            "B) File storage",
            "C) Block storage",
            "D) Network storage"
        ],
        "correct": "A",
        "explanation": "Object storage is correct because it stores data as objects." * 10,
        "supporting_fact": "Object storage stores data as objects.",
    }

    scorer = QuestionScorer(
        min_scores={"readability": 0.70}
    )

    is_acceptable, total, scores, issues = scorer.is_acceptable(question)

    assert is_acceptable is False
    assert scores["readability"] < 0.70
    assert any("Dimension readability" in issue for issue in issues)

def test_bad_distractors(scorer):
    # Violates distractor quality: Duplicate distractors
    question = {
        "question": "What is Object Storage?",
        "options": [
            "A) Object storage",
            "B) File storage",
            "C) File storage",
            "D) File storage"
        ],
        "correct": "A",
        "explanation": "Object storage stores data as objects.",
        "supporting_fact": "Object storage stores data as objects.",
    }

    scorer = QuestionScorer(
        min_scores={"distractors": 0.60}
    )

    is_acceptable, total, scores, issues = scorer.is_acceptable(question)

    assert is_acceptable is False
    assert scores["distractors"] < 0.60
    assert any("Dimension distractors" in issue for issue in issues)

def test_semantic_inconsistency(scorer):
    # Violates semantic consistency: Answer does not align with question
    question = {
        "question": "What is the fastest way to travel to Mars?",
        "options": [
            "A) Object storage",
            "B) File storage",
            "C) Block storage",
            "D) Network storage"
        ],
        "correct": "A",
        "explanation": "Object storage stores data as objects.",
        "supporting_fact": "Object storage stores data as objects.",
    }

    scorer = QuestionScorer(
        min_scores={"semantic": 0.90}
    )

    is_acceptable, total, scores, issues = scorer.is_acceptable(question)

    assert is_acceptable is False
    assert scores["semantic"] < 0.90
    assert any("Dimension semantic" in issue for issue in issues)

def test_unsupported_explanation(scorer):
    # Explanation not supported by supporting_fact
    question = {
        "question": "What is Object Storage?",
        "options": [
            "A) Object storage",
            "B) File storage",
            "C) Block storage",
            "D) Network storage"
        ],
        "correct": "A",
        "explanation": "It is made of cheese.",
        "supporting_fact": "Object storage stores data as objects.",
    }

    scorer = QuestionScorer(
        min_scores={"semantic": 0.80}
    )

    is_acceptable, total, scores, issues = scorer.is_acceptable(question)

    assert is_acceptable is False
    assert scores["semantic"] < 0.80
    assert any("Dimension semantic" in issue for issue in issues)

def test_invalid_schema(scorer):
    # Violates schema: Missing options
    question = {
        "question": "What is Object Storage?",
        "correct": "A",
        "explanation": "Object storage stores data as objects.",
        "supporting_fact": "Object storage stores data as objects.",
    }
    
    total, scores, issues = scorer.score_question(question)
    
    assert total < QUALITY_THRESHOLD, f"Expected invalid schema to score < {QUALITY_THRESHOLD}, got {total}"
    assert scores["schema"] == 0.0

def test_determinism(scorer):
    question = {
        "question": "What is Object Storage?",
        "options": ["A) A", "B) B", "C) C", "D) D"],
        "correct": "A",
        "explanation": "Object storage stores data as objects.",
        "supporting_fact": "Object storage stores data as objects.",
    }
    
    res1 = scorer.score_question(question)
    res2 = scorer.score_question(question)
    
    assert res1 == res2

def test_weighted_score_consistency(scorer):
    question = {
        "question": "What is Object Storage?",
        "options": ["A) A", "B) B", "C) C", "D) D"],
        "correct": "A",
        "explanation": "Object storage stores data as objects.",
        "supporting_fact": "Object storage stores data as objects.",
    }
    
    total, scores, issues = scorer.score_question(question)
    
    calculated_total = sum(scores[k] * DEFAULT_WEIGHTS.get(k, 0) for k in scores)
    
    assert pytest.approx(total) == calculated_total

def test_facts_argument_does_not_change_current_score(scorer):
    question = {
        "question": "What is Object Storage?",
        "options": ["A) A", "B) B", "C) C", "D) D"],
        "correct": "A",
        "explanation": "Object storage stores data as objects.",
        "supporting_fact": "Object storage stores data as objects.",
    }
    
    facts_pool = [{"fact": "unrelated fact"}]
    
    res_no_facts = scorer.score_question(question, [])
    res_with_facts = scorer.score_question(question, facts_pool)
    
    assert res_no_facts == res_with_facts

# --- New tests for min_scores infrastructure ---

def test_backward_compatibility_no_floors():
    scorer = QuestionScorer()
    assert scorer.min_scores == {}

def test_backward_compatibility_weights():
    weights = {"schema": 1.0}
    scorer = QuestionScorer(weights=weights)
    assert scorer.weights == weights

def test_backward_compatibility_min_score():
    scorer = QuestionScorer(min_acceptable_score=0.8)
    assert scorer.min_acceptable_score == 0.8

def test_passing_floor():
    question = {
        "question": "What is Object Storage?",
        "options": ["A) A", "B) B", "C) C", "D) D"],
        "correct": "A",
        "explanation": "Object storage stores data as objects.",
        "supporting_fact": "Object storage stores data as objects.",
    }
    scorer = QuestionScorer(min_scores={"schema": 0.5})
    is_acceptable, total, scores, issues = scorer.is_acceptable(question)
    assert is_acceptable is True

def test_failing_floor():
    # Schema check fails if question doesn't have required fields
    question = {
        "question": "What is Object Storage?",
        "correct": "A",
        "explanation": "Object storage stores data as objects.",
        "supporting_fact": "Object storage stores data as objects.",
    }
    # Schema score will be 0.0
    scorer = QuestionScorer(min_scores={"schema": 0.5})
    is_acceptable, total, scores, issues = scorer.is_acceptable(question)
    assert is_acceptable is False
    assert any("Dimension schema" in issue for issue in issues)

def test_multiple_floors():
    question = {
        "question": "What is Object Storage?",
        "correct": "A",
        "explanation": "Object storage stores data as objects.",
        "supporting_fact": "Object storage stores data as objects.",
    }
    # Both fail
    scorer = QuestionScorer(min_scores={"schema": 0.5, "semantic": 0.5})
    is_acceptable, total, scores, issues = scorer.is_acceptable(question)
    assert is_acceptable is False
    assert any("Dimension schema" in issue for issue in issues)

def test_score_question_unchanged():
    question = {
        "question": "What is Object Storage?",
        "options": ["A) A", "B) B", "C) C", "D) D"],
        "correct": "A",
        "explanation": "Object storage stores data as objects.",
        "supporting_fact": "Object storage stores data as objects.",
    }
    scorer_default = QuestionScorer()
    scorer_with_floor = QuestionScorer(min_scores={"schema": 0.5})
    
    assert scorer_default.score_question(question) == scorer_with_floor.score_question(question)
