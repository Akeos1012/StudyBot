"""
AI Study Companion - Main Application Entry Point.

This module sets up the FastAPI application and dependencies.
Business logic is delegated to services.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .rag.metadata_loader import MetadataLoader
from .quiz.quiz_generator import QuizGenerator
from .quiz.pool_manager import PoolManager
from .monitoring.pool_metrics import PoolMetrics
from .rag.retriever import Retriever
from .services.quiz_service import QuizService
from .api.routes import setup_routes
from .learning.mastery_service import MasteryService
from .learning.mastery_storage import MasteryStorage
from .learning.history_service import HistoryService
from .learning.history_storage import HistoryStorage
from .learning.analytics_service import LearningAnalyticsService
from .learning.recommendation_engine import RecommendationEngine

# Create FastAPI app
app = FastAPI(title="AI Study Companion")


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================
# Dependency Creation
# ============================

metadata_loader = MetadataLoader("sample_notes")

metadata = metadata_loader.load_metadata()


quiz_generator = QuizGenerator()

pool_metrics = PoolMetrics()

pool_manager = PoolManager(
    cache=quiz_generator.cache,
    generator=quiz_generator,
    retriever=Retriever(fact_cache=quiz_generator.fact_cache),
    pool_metrics=pool_metrics
)

history_storage = HistoryStorage()
history_service = HistoryService(storage=history_storage)
mastery_storage = MasteryStorage()
mastery_service = MasteryService(storage=mastery_storage)
analytics_service = LearningAnalyticsService(mastery_storage=mastery_storage, history_storage=history_storage)
recommendation_engine = RecommendationEngine()

quiz_service = QuizService(
    metadata_loader=metadata_loader, 
    quiz_generator=quiz_generator,
    pool_manager=pool_manager,
    mastery_service=mastery_service,
    history_service=history_service,
    analytics_service=analytics_service,
    recommendation_engine=recommendation_engine
)


# ============================
# Routes
# ============================

router = setup_routes(quiz_service, metadata_loader, metadata)

app.include_router(router)


# Direct execution support
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
