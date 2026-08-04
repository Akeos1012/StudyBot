from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from app.models.api_schema import (
    MasteryResponse,
    ProgressResponse,
    AnalyticsSummaryResponse,
    TrendResponse,
    WeakTopicResponse,
    RecommendationResponse
)

def setup_analytics_routes(analytics_service, recommendation_service=None):
    router = APIRouter(prefix="/analytics", tags=["analytics"])

    @router.get("/mastery", response_model=MasteryResponse)
    async def get_mastery(user_id: Optional[str] = Header(None, alias="X-User-ID")):
        if not user_id:
            raise HTTPException(status_code=400, detail="Missing X-User-ID")
        return analytics_service.get_mastery_summary(user_id)

    @router.get("/weak-topics", response_model=list[WeakTopicResponse])
    async def get_weak_topics(user_id: Optional[str] = Header(None, alias="X-User-ID")):
        if not user_id:
            raise HTTPException(status_code=400, detail="Missing X-User-ID")
        return analytics_service.get_weak_topics(user_id)

    @router.get("/progress", response_model=ProgressResponse)
    async def get_progress(user_id: Optional[str] = Header(None, alias="X-User-ID")):
        if not user_id:
            raise HTTPException(status_code=400, detail="Missing X-User-ID")
        return analytics_service.get_progress_summary(user_id)

    @router.get("/trend", response_model=TrendResponse)
    async def get_trend(user_id: Optional[str] = Header(None, alias="X-User-ID"), days: int = 30):
        if not user_id:
            raise HTTPException(status_code=400, detail="Missing X-User-ID")
        return analytics_service.get_learning_trend(user_id, days)

    @router.get("/summary", response_model=AnalyticsSummaryResponse)
    async def get_summary(user_id: Optional[str] = Header(None, alias="X-User-ID")):
        if not user_id:
            raise HTTPException(status_code=400, detail="Missing X-User-ID")
        return {
            "mastery": analytics_service.get_mastery_summary(user_id),
            "progress": analytics_service.get_progress_summary(user_id),
            "weak_topics": analytics_service.get_weak_topics(user_id)
        }

    @router.get("/recommendations", response_model=RecommendationResponse)
    async def get_recommendations(user_id: Optional[str] = Header(None, alias="X-User-ID")):
        if not user_id:
            raise HTTPException(status_code=400, detail="Missing X-User-ID")
        if not recommendation_service:
            raise HTTPException(status_code=501, detail="Recommendation service not configured")
        return {"recommendations": recommendation_service.get_recommendations(user_id)}

    return router
