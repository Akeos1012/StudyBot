"""
AI Study Companion - Main Application Entry Point.

This module sets up the FastAPI application and dependencies.
Business logic is delegated to services.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .rag.metadata_loader import MetadataLoader
from .quiz.generation.quiz_generator import QuizGenerator
from .quiz.storage.pool_manager import PoolManager
from .monitoring.pool_metrics import PoolMetrics
from .rag.retriever import Retriever
from .services.quiz_service import QuizService
from .services.quiz_session_service import QuizSessionService
from .quiz.storage.session_storage import QuizSessionStorage
from .services.smart_reviewer_service import SmartReviewerService
from .api.quiz_routes import setup_routes
from .learning.recommendation.recommendation_engine import RecommendationEngine

from .learning.analytics.db_manager import DBManager
from .learning.analytics.analytics_service import LearningAnalyticsService as SQLiteAnalyticsService
from .learning.analytics.analytics_repository import AnalyticsRepository
from .learning.recommendation.recommendation_service import RecommendationService
from .api.analytics_routes import setup_analytics_routes

# Tutor Imports
from .tutor.query_preprocessor import QueryPreprocessor
from .tutor.intent_classifier import IntentClassifier
from .tutor.query_retriever import QueryRetriever
from .tutor.fallback_handler import FallbackHandler
from .tutor.answer_builder import AnswerBuilder
from .tutor.source_linker import SourceLinker
from .services.tutor_service import TutorService
from .quiz.generation.llm_client import LLMClient
from .api.tutor_routes import setup_tutor_routes

from app.config import settings

# Create FastAPI app
app = FastAPI(title="AI Study Companion")


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
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
    pool_metrics=pool_metrics,
)

# Analytics components
db_manager = DBManager()
analytics_repository = AnalyticsRepository(db_manager)

new_analytics_service = SQLiteAnalyticsService(analytics_repository)

recommendation_engine = RecommendationEngine()
recommendation_service = RecommendationService(
    new_analytics_service, recommendation_engine
)

# Session components
quiz_session_storage = QuizSessionStorage(db_manager)
quiz_session_service = QuizSessionService(quiz_session_storage)

# Tutor components
preprocessor = QueryPreprocessor()
intent_classifier = IntentClassifier()
query_retriever = QueryRetriever(
    retriever=Retriever(fact_cache=quiz_generator.fact_cache)
)
fallback_handler = FallbackHandler()
answer_builder = AnswerBuilder(llm_client=LLMClient())
source_linker = SourceLinker()

tutor_service = TutorService(
    query_preprocessor=preprocessor,
    intent_classifier=intent_classifier,
    query_retriever=query_retriever,
    fallback_handler=fallback_handler,
    answer_builder=answer_builder,
    source_linker=source_linker,
)

smart_reviewer_service = SmartReviewerService(fact_cache=quiz_generator.fact_cache)

quiz_service = QuizService(
    metadata_loader=metadata_loader,
    quiz_generator=quiz_generator,
    pool_manager=pool_manager,
    recommendation_engine=recommendation_engine,
    quiz_session_service=quiz_session_service,
    analytics_repository=analytics_repository,
    analytics_service=new_analytics_service,
)


# ============================
# Routes
# ============================

router = setup_routes(
    quiz_service,
    quiz_session_service,
    metadata_loader,
    metadata,
    smart_reviewer_service=smart_reviewer_service,
)

app.include_router(router)

tutor_router = setup_tutor_routes(tutor_service)
app.include_router(tutor_router)

analytics_router = setup_analytics_routes(new_analytics_service, recommendation_service)
app.include_router(analytics_router)


# Direct execution support
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
    )
