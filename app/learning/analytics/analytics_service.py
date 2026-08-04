from typing import List, Dict, Any
from app.learning.analytics.analytics_repository import AnalyticsRepository


class LearningAnalyticsService:
    def __init__(self, repository: AnalyticsRepository):
        self.repository = repository

    def get_mastery_summary(self, user_id: str) -> Dict[str, Any]:
        records = self.repository.get_mastery_records(user_id)
        if not records:
            return {"overall_mastery": 0.0, "total_attempts": 0, "concepts_tracked": 0}

        total_mastery = sum(r["mastery_score"] for r in records)
        total_attempts = sum(r["attempts"] for r in records)

        return {
            "overall_mastery": round(total_mastery / len(records), 2),
            "total_attempts": total_attempts,
            "concepts_tracked": len(records),
            "last_updated": (
                max(r.get("last_updated") for r in records if r.get("last_updated"))
                if any(r.get("last_updated") for r in records)
                else None
            ),
        }

    def get_weak_topics(
        self, user_id: str, threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        records = self.repository.get_mastery_records(user_id)
        weak_concepts = [r for r in records if r["mastery_score"] < threshold]

        return [
            {
                "topic": r["concept"],
                "mastery": r["mastery_score"],
                "priority": "high" if r["mastery_score"] < 0.3 else "medium",
            }
            for r in weak_concepts
        ]

    def get_progress_summary(self, user_id: str) -> Dict[str, Any]:
        metrics = self.repository.get_activity_metrics(user_id)
        total = metrics["total_questions"] or 0
        correct = metrics["correct_answers"] or 0
        accuracy = (correct / total * 100) if total > 0 else 0.0
        events = self.repository.get_learning_events(user_id, days=30)
        topics_studied = sorted(
            {event.get("topic") for event in events if event.get("topic")}
        )

        return {
            "total_questions_answered": total,
            "correct_answers": correct,
            "accuracy_percentage": round(accuracy, 2),
            "topics_studied": topics_studied,
        }

    def get_activity_metrics(self, user_id: str) -> Dict[str, Any]:
        metrics = self.repository.get_activity_metrics(user_id)
        total = metrics["total_questions"] or 0
        sessions = metrics["total_sessions"] or 0

        return {
            "total_sessions": sessions,
            "active_days": metrics["active_days"],
            "questions_per_session": (
                round(total / sessions, 2) if sessions > 0 else 0.0
            ),
        }

    def get_learning_trend(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        events = self.repository.get_learning_events(user_id, days)
        if not events:
            return {"period": f"{days}_days", "trend": [], "direction": "stable"}

        grouped: Dict[str, Dict[str, Any]] = {}
        for event in events:
            date_key = event.get("timestamp", "")[:10]
            if not date_key:
                continue
            bucket = grouped.setdefault(
                date_key,
                {
                    "date": date_key,
                    "accuracy": 0.0,
                    "mastery": 0.0,
                    "count": 0,
                    "correct": 0,
                },
            )
            bucket["count"] += 1
            if event.get("correct") in (1, True):
                bucket["correct"] += 1

        trend = []
        for date_key in sorted(grouped):
            bucket = grouped[date_key]
            accuracy = (
                round((bucket["correct"] / bucket["count"]) * 100, 2)
                if bucket["count"]
                else 0.0
            )
            trend.append({"date": date_key, "accuracy": accuracy, "mastery": accuracy})

        if not trend:
            return {"period": f"{days}_days", "trend": [], "direction": "stable"}

        direction = (
            "improving"
            if trend[-1]["accuracy"] >= trend[0]["accuracy"]
            else "declining"
        )
        return {"period": f"{days}_days", "trend": trend, "direction": direction}
