import pytest
from app.services.quiz_service import QuizService
from app.quiz.storage.question_cache import QuestionCache
from unittest.mock import MagicMock

def test_cache_bucket_consistency(tmp_path):
    # Verify that get_or_generate_questions reads and writes using "multiple_choice"
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
    
    # Mock generator to return questions
    service.generate_questions_for_topic = MagicMock(return_value=[
        {
            "question": "Generated Question 1",
            "options": ["A) First", "B) Second", "C) Third", "D) Fourth"],
            "correct": "A",
            "question_type": "multiple_choice",
            "question_id": "gen-1",
            "correct_text": "Correct A",
            "explanation": "Valid explanation A",
            "supporting_fact": "This is a valid supporting fact A",
            "source_note": "Note",
            "fact_id": "fact-1",
            "concept": "Concept"
        }
    ])
    
    # Call get_or_generate_questions with count=1
    result = service.get_or_generate_questions("AI", "", "medium", count=1)
    
    assert len(result) == 1
    assert result[0].get("question") == "Generated Question 1"
    
    pool = cache.get_pool("AI", "", "medium", "multiple_choice")
    assert len(pool) == 1
