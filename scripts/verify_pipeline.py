from app.services.quiz_service import QuizService
from app.rag.metadata_loader import MetadataLoader
from app.quiz.quiz_generator import QuizGenerator
from app.quiz.pool_manager import PoolManager
from app.learning.mastery_service import MasteryService
from app.learning.mastery_storage import MasteryStorage
from app.learning.history_service import HistoryService
from app.learning.history_storage import HistoryStorage
from app.learning.analytics_service import LearningAnalyticsService
from app.learning.recommendation_engine import RecommendationEngine
import json
import logging

logging.basicConfig(level=logging.INFO)

# Initialize
metadata_loader = MetadataLoader("sample_notes")
quiz_generator = QuizGenerator()
pool_manager = PoolManager(
    cache=quiz_generator.cache,
    generator=quiz_generator,
    retriever=None, # Dummy for script
    pool_metrics=None # Dummy for script
)
mastery_storage = MasteryStorage()
history_storage = HistoryStorage()

mastery_service = MasteryService(storage=mastery_storage)
history_service = HistoryService(storage=history_storage)
analytics_service = LearningAnalyticsService(mastery_storage=mastery_storage, history_storage=history_storage)
recommendation_engine = RecommendationEngine()

quiz_service = QuizService(
    metadata_loader, 
    quiz_generator, 
    pool_manager, 
    mastery_service, 
    history_service,
    analytics_service,
    recommendation_engine
)

# Trigger
topic = "Algorithms"
print(f"Triggering pipeline for {topic}")
# This will call the actual generation
questions = quiz_service.generate_questions_for_topic(topic, count=3)

print(f"Generated {len(questions)} questions")
# Print first question for validation
if questions:
    print(json.dumps(questions[0], indent=2))
else:
    print("No questions generated.")
