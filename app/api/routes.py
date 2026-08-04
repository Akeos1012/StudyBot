"""
API Routes - FastAPI endpoint definitions.

This module contains HTTP endpoint handlers.
Business logic is delegated to services.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Header
from typing import Optional
import logging

logger = logging.getLogger(__name__)

from app.models.user_context import UserContext
from app.models.smart_reviewer_schema import SmartReviewerResult
from app.models.api_schema import (
    QuizRequest,
    FillBlankRequest,
    QuizResponse,
    AnswerSubmission,
    AnswerResponse,
    ReviewRequest,
)

def setup_routes(quiz_service, quiz_session_service, metadata_loader, metadata, smart_reviewer_service=None):
    router = APIRouter()
    
    @router.get("/knowledge/topics")
    async def get_knowledge_topics():
        return quiz_service.get_knowledge_summary()

    @router.post("/quiz/session/create")
    async def create_session(
        request: QuizRequest,
        user_id: Optional[str] = Header(None, alias="X-User-ID")
    ):
        user_context = UserContext(user_id=user_id)
        session = quiz_service.create_quiz_session(
            user_id=user_id,
            topic=request.topic,
            difficulty=request.difficulty,
            count=request.count,
            fresh=request.fresh,
            adaptive=request.adaptive
        )
        full_questions = []
        for qid in session.question_ids:
            q = quiz_service.quiz_generator.cache.get_question_by_id(qid)
            if q:
                full_questions.append(q)

        return {
            "session_id": session.session_id,
            "topic": session.topic,
            "difficulty": session.difficulty,
            "status": session.status.value,
            "questions": full_questions
        }

    @router.get("/quiz/session/{session_id}")
    async def get_session(session_id: str, user_id: Optional[str] = Header(None, alias="X-User-ID")):
        session = quiz_session_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if user_id and session.user_id != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")
        full_questions = []
        for qid in session.question_ids:
            q = quiz_service.quiz_generator.cache.get_question_by_id(qid)
            if q:
                full_questions.append(q)

        return {
            "session_id": session.session_id,
            "status": session.status.value,
            "topic": session.topic,
            "difficulty": session.difficulty,
            "current_question_index": session.current_question_index,
            "questions": full_questions,
            "progress": {
                "answered": session.current_question_index,
                "total": len(session.question_ids)
            }
        }

    @router.post("/quiz/session/{session_id}/answer")
    async def submit_session_answer(
        session_id: str,
        request: AnswerSubmission,
        user_id: Optional[str] = Header(None, alias="X-User-ID")
    ):
        user_context = UserContext(user_id=user_id)
        try:
            # Need to validate user_id in submit_session_answer? 
            # The service does not do it, but the route could.
            # For now, let's keep it consistent with the existing submit_session_answer logic 
            # which relies on user_context (which is built from user_id).
            result = quiz_service.submit_session_answer(session_id, request.question_id, request.answer, user_context)
            session = quiz_session_service.get_session(session_id)
            return {
                **result,
                "progress": {
                    "answered": session.current_question_index,
                    "total": len(session.question_ids)
                },
                "completed": session.status == SessionStatus.COMPLETED
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
            
    @router.patch("/quiz/session/{session_id}/complete")
    async def complete_session(session_id: str, user_id: Optional[str] = Header(None, alias="X-User-ID")):
        session = quiz_session_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if user_id and session.user_id != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")
        quiz_session_service.complete_session(session_id)
        session = quiz_session_service.get_session(session_id)
        return {
            "status": session.status.value,
            "completed_at": session.completed_at
        }

    @router.post(
        "/generate-fill-blank",
        response_model=QuizResponse
    )
    async def generate_fill_blank(request: FillBlankRequest):

        topic = request.topic or "Database"

        subtopic = request.subtopic or ""

        difficulty = request.difficulty or "medium"

        fresh = request.fresh

        questions = quiz_service.generate_fill_blank_questions(
            topic=topic,
            subtopic=subtopic,
            difficulty=difficulty,
            count=request.count,
        )

        if not questions:
            raise HTTPException(
                status_code=404,
                detail=f"No fill blank questions found for topic: {topic}"
            )

        return {
            "success": True,
            "topic": topic,
            "subtopic": subtopic if subtopic else None,
            "difficulty": difficulty,
            "question_type": "fill_blank",
            "count": len(questions),
            "questions": questions,
            "source_notes": list(
                set(
                    q.get("source_note")
                    for q in questions
                    if q.get("source_note")
                )
            ),
        }

    @router.post(
        "/quiz/submit-answer",
        response_model=AnswerResponse
    )
    async def submit_answer(
        request: AnswerSubmission,
        user_id: Optional[str] = Header(None, alias="X-User-ID")
    ):
        user_context = UserContext(user_id=user_id)
        
        result = quiz_service.record_answer(
            request.question_id,
            request.answer,
            user_context=user_context
        )

        return result

    @router.post(
        "/quiz/review",
        response_model=SmartReviewerResult
    )
    async def review_answer(
        request: ReviewRequest,
        user_id: Optional[str] = Header(None, alias="X-User-ID")
    ):
        """
        Endpoint for Smart Reviewer feedback.
        Retrieves cached question and generates a rich review.
        """
        if not smart_reviewer_service:
            raise HTTPException(
                status_code=501,
                detail="Smart Reviewer service not configured"
            )

        # 1. Retrieve question artifact
        question = quiz_service.quiz_generator.cache.get_question_by_id(request.question_id)
        
        if not question:
            raise HTTPException(
                status_code=404,
                detail=f"Question ID {request.question_id} not found in cache"
            )

        # 2. Generate review
        try:
            review = smart_reviewer_service.generate_review(
                question, 
                request.user_answer
            )
            return review
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Smart Reviewer failed: {e}")
            raise HTTPException(
                status_code=500,
                detail="Internal error during review generation"
            )

    @router.post("/refresh-notes")
    async def refresh_notes():

        try:
            metadata_loader.metadata_file.unlink(missing_ok=True)
        except Exception:
            pass

        new_metadata = metadata_loader.load_metadata()

        topics = sorted(list(set(note["topic"] for note in new_metadata)))

        return {
            "message": "Notes refreshed successfully!",
            "total_notes": len(new_metadata),
            "topics": topics,
        }

    @router.get("/cache/status")
    async def cache_status():

        return {"message": "Cache status endpoint ready", "status": "ok"}

    return router
