import pytest
from app.services.quiz_service import QuizService
from app.quiz.storage.question_cache import QuestionCache
from unittest.mock import MagicMock

def test_question_id_invariant(tmp_path):
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
    
    # Populate mock cache with a question missing question_id
    cache.add_to_pool(
        "AI", "", "medium", "multiple_choice",
        [{
            "question": "Cached Question No ID",
            "options": ["A) First", "B) Second", "C) Third", "D) Fourth"],
            "correct": "A",
            "question_type": "multiple_choice",
            # question_id missing
            "correct_text": "Correct A",
            "explanation": "Valid explanation A",
            "supporting_fact": "This is a valid supporting fact A",
            "source_note": "Note",
            "fact_id": "fact-1",
            "concept": "Concept"
        }]
    )
    
    # Request question. Ensure get_or_generate_questions assigns it.
    result = service.get_or_generate_questions("AI", "", "medium", count=1)
    
    assert len(result) == 1
    assert "question_id" in result[0]
    assert result[0]["question_id"] is not None
    assert result[0]["question_id"] == "cb403bace97d73ec84b68785eee1c2c2" # MD5 of "Cached Question No ID"
