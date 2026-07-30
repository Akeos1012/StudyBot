
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from app.monitoring.quiz_metrics import QuizMetrics

@dataclass
class MetricsContext:
    quiz_metrics: QuizMetrics
    topic: str
    expansion_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
