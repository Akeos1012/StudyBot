"""
API Routes - FastAPI endpoint definitions.

This module contains HTTP endpoint handlers.
Business logic is delegated to services.
"""

from fastapi import APIRouter, HTTPException

from app.models.api_schema import (
    QuizRequest,
    FillBlankRequest,
    QuizResponse,
)

def setup_routes(quiz_service, metadata_loader, metadata):
    router = APIRouter()
    """
    Configure routes with application dependencies.

    Dependencies are created in main.py:
    - QuizService
    - MetadataLoader
    - Metadata
    """

    @router.get("/")
    async def root():
        return {"message": "AI Study Companion API"}

    @router.get("/topics")
    async def get_topics():
        topics = list(set(note["topic"] for note in metadata))

        return {"topics": sorted(topics)}

    @router.get("/topics/{topic}/subtopics")
    async def get_subtopics(topic: str):
        subtopics = metadata_loader.get_subtopics_by_topic(topic)

        if not subtopics:
            raise HTTPException(404, f"No subtopics found for topic: {topic}")

        return {"topic": topic, "subtopics": subtopics}

    @router.get("/topics/{topic}/{subtopic}")
    async def get_notes_by_subtopic(topic: str, subtopic: str):
        notes = metadata_loader.get_notes_by_subtopic(topic, subtopic)

        if not notes:
            raise HTTPException(404, f"No notes found for {topic} > {subtopic}")

        return {"topic": topic, "subtopic": subtopic, "notes": notes}

    @router.get("/notes/{topic}")
    async def get_notes_by_topic(topic: str):
        filtered = [n for n in metadata if n["topic"].lower() == topic.lower()]

        if not filtered:
            raise HTTPException(404, f"No notes found for topic: {topic}")

        return filtered

    @router.post("/quiz/generate", response_model=QuizResponse)
    async def generate_quiz(request: QuizRequest):

        topic = request.topic

        subtopic = request.subtopic
        count = request.count
        difficulty = request.difficulty
        fresh = request.fresh

        questions = quiz_service.get_or_generate_questions(
            topic=topic,
            subtopic=subtopic,
            difficulty=difficulty,
            count=count,
            fresh=fresh,
            question_type="multiple",
        )

        return {
            "topic": topic,
            "subtopic": subtopic if subtopic else None,
            "questions": questions,
            "source_notes": ["Pool sample"],
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
            count=3,
        )

        return {
            "topic": topic,
            "subtopic": subtopic if subtopic else None,
            "questions": questions,
            "source_notes": ["Pool sample"],
        }

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
