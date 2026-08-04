from typing import List, Dict, Any
from app.learning.analytics.analytics_service import LearningAnalyticsService
from app.learning.recommendation_engine import RecommendationEngine

class RecommendationService:
    def __init__(self, analytics_service: LearningAnalyticsService, recommendation_engine: RecommendationEngine):
        self.analytics_service = analytics_service
        self.recommendation_engine = recommendation_engine

    def get_recommendations(self, user_id: str) -> List[Dict[str, Any]]:
        # Get data from analytics
        weak_topics = self.analytics_service.get_weak_topics(user_id)
        
        # Determine recommendations based on simple rules
        recommendations = []
        for topic in weak_topics:
            # Deterministic reason generation
            reason = "Low mastery detected" if topic["mastery"] < 0.4 else "Needs reinforcement"
            
            recommendations.append({
                "topic": topic["topic"],
                "reason": reason,
                "priority": topic["priority"],
                "suggested_action": f"Review {topic['topic']} concepts"
            })
            
        return recommendations
