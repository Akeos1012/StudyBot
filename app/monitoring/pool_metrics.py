from dataclasses import dataclass, field
import time
from typing import Dict, Any

@dataclass
class PoolMetrics:
    """
    Tracks PoolManager health and expansion events.
    In-memory counters only.
    """
    health_checks: int = 0
    healthy_count: int = 0
    unhealthy_count: int = 0
    
    expansion_attempts: int = 0
    expansion_success: int = 0
    expansion_failure: int = 0
    
    total_questions_added: int = 0
    total_expansion_time_ms: float = 0.0

    def record_health_check(self, healthy: bool):
        self.health_checks += 1
        if healthy:
            self.healthy_count += 1
        else:
            self.unhealthy_count += 1

    def record_expansion_attempt(self):
        self.expansion_attempts += 1

    def record_expansion_success(self, questions_added: int, duration_ms: float):
        self.expansion_success += 1
        self.total_questions_added += questions_added
        self.total_expansion_time_ms += duration_ms

    def record_expansion_failure(self):
        self.expansion_failure += 1

    def report(self) -> Dict[str, Any]:
        return {
            "health_checks": self.health_checks,
            "healthy_count": self.healthy_count,
            "unhealthy_count": self.unhealthy_count,
            "expansion_attempts": self.expansion_attempts,
            "expansion_success": self.expansion_success,
            "expansion_failure": self.expansion_failure,
            "total_questions_added": self.total_questions_added,
            "total_expansion_time_ms": round(self.total_expansion_time_ms, 2)
        }
