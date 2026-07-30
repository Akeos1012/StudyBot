"""
API Routes - FastAPI endpoint definitions.

This module contains HTTP endpoint handlers.
Business logic is delegated to services.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
import logging

logger = logging.getLogger(__name__)

from app.models.api_schema import (
    QuizRequest,
    FillBlankRequest,
    QuizResponse,
    AnswerSubmission,
    AnswerResponse,
)

def setup_routes(quiz_service, metadata_loader, metadata):
    router = APIRouter()
    # ...
    @router.post("/quiz/generate", response_model=QuizResponse)
    async def generate_quiz(request: QuizRequest, background_tasks: BackgroundTasks):

        try:
            topic = request.topic

            subtopic = request.subtopic
            count = request.count
            difficulty = request.difficulty
            fresh = request.fresh

            # Proactive Pool Management
            pool_manager = quiz_service.pool_manager
            health = pool_manager.should_expand_pool(topic)
            if health.get("expand", False):
                if pool_manager.try_start_expansion(topic):
                    logger.info(f"Background pool expansion triggered for {topic}")
                    background_tasks.add_task(pool_manager.expand_pool, topic)
            
            questions = quiz_service.get_or_generate_questions(
                topic=topic,
                subtopic=subtopic,
                difficulty=difficulty,
                count=count,
                fresh=fresh,
                question_type="multiple",
            )

            if not questions:
                raise HTTPException(
                    status_code=404,
                    detail=f"No questions found for topic: {topic}"
                )

            return {
                "success": True,
                "topic": topic,
                "subtopic": subtopic if subtopic else None,
                "difficulty": difficulty,
                "question_type": "multiple",
                "count": len(questions),
                "questions": questions,
                "source_notes": sorted(
                    {
                        q.get("source_note")
                        for q in questions
                        if q.get("source_note")
                    }
                )
            }

        except HTTPException:
            raise

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Quiz generation failed: {str(e)}"
            )

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
    async def submit_answer(request: AnswerSubmission):

        result = quiz_service.record_answer(
            request.question_id,
            request.answer
        )

        return result

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
