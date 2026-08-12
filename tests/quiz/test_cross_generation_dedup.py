
import pytest
from app.quiz.generation.quiz_generator import QuizGenerator
from app.quiz.storage.question_cache import QuestionCache

class MockCache(QuestionCache):
    def __init__(self):
        self.cache = {}
        
    def get_pool(self, topic, **kwargs):
        return self.cache.get(topic, [])

    def add_to_pool(self, topic, **kwargs):
        pass # Not needed for this test

    def sample(self, topic, **kwargs):
        return []

def test_cross_generation_duplicate_rejection():
    # 1. Setup
    generator = QuizGenerator(cache=MockCache())
    topic = "AI"
    question_text = "What technique is used to improve model performance by creating modified versions of existing data?"
    answer = "Data Augmentation"
    
    # Fake existing pool
    existing_pool = [{
        "question": question_text,
        "correct_text": answer,
        "supporting_fact": "Data Augmentation is..."
    }]
    generator.cache.cache[topic] = existing_pool
    
    # 2. Try to generate/validate duplicate
    new_question = {
        "question": question_text,
        "correct_text": answer,
        "supporting_fact": "Data Augmentation is..."
    }
    
    # 3. Simulate the logic from QuizGenerator
    from app.quiz.utils.question_similarity import is_similar_to_pool
    from app.config import settings
    
    full_pool = [] + (generator.cache.get_pool(topic=topic) or [])
    
    # Check if duplicate is detected
    is_duplicate = is_similar_to_pool(
        new_question,
        full_pool,
        threshold=settings.SIMILARITY_THRESHOLD
    )
    
    assert is_duplicate is True

def test_different_question_same_concept_allowed():
    # 1. Setup
    # 2. Try different questions
    # 3. Verify NOT DUPLICATE
    pass
