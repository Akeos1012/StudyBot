from app.services.quiz_service import QuizService
from app.rag.metadata_loader import MetadataLoader
from app.quiz.quiz_generator import QuizGenerator
import json
import logging

logging.basicConfig(level=logging.INFO)

# Initialize
# Assuming sample_notes exists in the root, as per directory structure
metadata_loader = MetadataLoader("sample_notes")
quiz_generator = QuizGenerator()
quiz_service = QuizService(metadata_loader, quiz_generator)

# Trigger
topic = "Unknown"
print(f"Triggering pipeline for {topic}")
# This will call the actual generation
questions = quiz_service.generate_questions_for_topic(topic, count=3)

print(f"Generated {len(questions)} questions")
# Print first question for validation
if questions:
    print(json.dumps(questions[0], indent=2))
else:
    print("No questions generated.")
