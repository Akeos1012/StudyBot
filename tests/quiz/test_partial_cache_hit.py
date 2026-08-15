import pytest
from app.services.quiz_service import QuizService
from app.quiz.storage.question_cache import QuestionCache
from unittest.mock import MagicMock

def test_partial_cache_hit(tmp_path):
    cache = QuestionCache(cache_file=str(tmp_path / "test_cache.json"))
    quiz_gen_mock = MagicMock()
    quiz_gen_mock.cache = cache
    service = QuizService(
        metadata_loader=MagicMock(),
        quiz_generator=quiz_gen_mock,
        pool_manager=MagicMock(),
        recommendation_engine=MagicMock(),
        quiz_session_service=MagicMock(),
        analytics_repository=MagicMock(),
        analytics_service=MagicMock()
    )
    
    # Pre-populate cache with 1 valid question
    cache.add_to_pool(
        "AI", "", "medium", "multiple_choice",
        [{
            "question": "Cached Question",
            "options": ["A) First", "B) Second", "C) Third", "D) Fourth"],
            "correct": "A",
            "question_type": "multiple_choice",
            "question_id": "cached-1",
            "correct_text": "Correct A",
            "explanation": "Valid explanation A",
            "supporting_fact": "This is a valid supporting fact A",
            "source_note": "Note",
            "fact_id": "fact-1",
            "concept": "Concept"
        }]
    )
    
    # Mock generator to return 2 questions
    service.generate_questions_for_topic = MagicMock(return_value=[
        {
            "question": "Gen Question 1",
            "options": ["A) First", "B) Second", "C) Third", "D) Fourth"],
            "correct": "A",
            "question_type": "multiple_choice",
            "question_id": "gen-1",
            "correct_text": "Correct A",
            "explanation": "Valid explanation B",
            "supporting_fact": "This is a valid supporting fact B",
            "source_note": "Note",
            "fact_id": "fact-2",
            "concept": "Concept"
        },
        {
            "question": "Gen Question 2",
            "options": ["A) First", "B) Second", "C) Third", "D) Fourth"],
            "correct": "B",
            "question_type": "multiple_choice",
            "question_id": "gen-2",
            "correct_text": "Correct B",
            "explanation": "Valid explanation C",
            "supporting_fact": "This is a valid supporting fact C",
            "source_note": "Note",
            "fact_id": "fact-3",
            "concept": "Concept"
        }
    ])
    
    # Request 3 questions
    result = service.get_or_generate_questions("AI", "", "medium", count=3)
    
    # Verify we got exactly 3 questions
    assert len(result) == 3
    
    # The result should contain the cached question + the 2 generated questions
    ids = [q["question_id"] for q in result]
    assert "cached-1" in ids
    assert "gen-1" in ids
    assert "gen-2" in ids
