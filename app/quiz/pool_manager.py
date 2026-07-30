import logging
import time
import threading
import uuid
from typing import Dict, Any, List, Set
from app.quiz.question_cache import QuestionCache
from app.quiz.quiz_generator import QuizGenerator
from app.rag.retriever import Retriever
from app.monitoring.pool_metrics import PoolMetrics
from app.monitoring.quiz_metrics import QuizMetrics
from app.monitoring.metrics_context import MetricsContext
# ...

logger = logging.getLogger(__name__)

class PoolManager:
    TARGET_DIFFICULTY = {"easy": 0.3, "medium": 0.5, "hard": 0.2}
    TARGET_TYPES = {"multiple_choice": 0.7, "fill_blank": 0.3}

    def __init__(
        self,
        cache: QuestionCache,
        generator: QuizGenerator,
        retriever: Retriever,
        pool_metrics: PoolMetrics
    ):
        self.cache = cache
        self.generator = generator
        self.retriever = retriever
        self.pool_metrics = pool_metrics
        self.min_pool_size = 5 
        
        # Expansion state tracking
        self._expansion_lock = threading.Lock()
        self._expanding_topics: Set[str] = set()

    def is_expanding(self, topic: str) -> bool:
        with self._expansion_lock:
            return topic in self._expanding_topics

    def try_start_expansion(self, topic: str) -> bool:
        with self._expansion_lock:
            if topic in self._expanding_topics:
                return False
            self._expanding_topics.add(topic)
            return True

    def finish_expansion(self, topic: str):
        with self._expansion_lock:
            self._expanding_topics.discard(topic)

    def calculate_target_pool_size(self, topic: str) -> Dict[str, Any]:
        facts = self.retriever.retrieve(topic=topic, limit=1000)
        available_facts = len(facts)
        
        target_size = max(self.min_pool_size, int(available_facts * 0.5))
        
        return {
            "topic": topic,
            "target_size": target_size,
            "available_facts": available_facts,
            "reason": [f"Scaled based on {available_facts} available facts"] if available_facts > 0 else ["No facts available, using min threshold"]
        }

    def check_pool_health(self, topic: str) -> Dict[str, Any]:
        pool_size = self._get_topic_pool_size(topic)
        
        status = "healthy"
        issues = []
        if pool_size < self.min_pool_size:
            status = "needs_expansion"
            issues.append(f"Pool size {pool_size} is below threshold {self.min_pool_size}")
            
        self.pool_metrics.record_health_check(healthy=(status == "healthy"))

        return {
            "topic": topic,
            "status": status,
            "pool_size": pool_size,
            "issues": issues
        }

    def should_expand_pool(self, topic: str) -> Dict[str, Any]:
        target = self.calculate_target_pool_size(topic)["target_size"]
        current = self._get_topic_pool_size(topic)
        reasons = []
        
        if current < target:
            reasons.append(f"Pool size {current} below target {target}")
            
        distribution = self.analyze_distribution(topic)
        if distribution["total"] > 0:
            if distribution["difficulty"].get("hard", 0) == 0:
                reasons.append("Missing hard questions")

        return {
            "expand": len(reasons) > 0,
            "reasons": reasons
        }

    def _get_topic_pool_size(self, topic: str) -> int:
        total = 0
        difficulties = ["easy", "medium", "hard"]
        question_types = ["multiple_choice", "fill_blank"]
        for difficulty in difficulties:
            for qtype in question_types:
                total += self.cache.get_pool_size(
                    topic=topic,
                    subtopic="",
                    difficulty=difficulty,
                    qtype=qtype
                )
        return total

    def calculate_missing_questions(self, topic: str) -> Dict[str, Any]:
        target_info = self.calculate_target_pool_size(topic)
        target = target_info["target_size"]
        dist = self.analyze_distribution(topic)
        
        missing_difficulty = {
            d: max(0, int(target * ratio) - dist["difficulty"].get(d, 0))
            for d, ratio in self.TARGET_DIFFICULTY.items()
        }
        
        missing_types = {
            t: max(0, int(target * ratio) - dist["types"].get(t, 0))
            for t, ratio in self.TARGET_TYPES.items()
        }
        
        return {
            "total_missing": sum(missing_difficulty.values()),
            "difficulty": missing_difficulty,
            "types": missing_types
        }

    def analyze_distribution(self, topic: str) -> Dict[str, Any]:
        questions = self.cache.sample(
            topic=topic,
            count=self._get_topic_pool_size(topic)
        ) or []
        
        distribution = {
            "total": len(questions),
            "types": {},
            "difficulty": {},
            "concepts": {}
        }
        
        for q in questions:
            q_type = q.get("type", "unknown")
            difficulty = q.get("difficulty", "unknown")
            concept = q.get("concept", "unknown")
            
            distribution["types"][q_type] = distribution["types"].get(q_type, 0) + 1
            distribution["difficulty"][difficulty] = distribution["difficulty"].get(difficulty, 0) + 1
            distribution["concepts"][concept] = distribution["concepts"].get(concept, 0) + 1
            
        return distribution

    def generate_expansion_plan(self, topic: str, missing_counts: Dict[str, Any]) -> List[Dict[str, Any]]:
        plan = []
        for qtype, count in missing_counts.get("types", {}).items():
            if count > 0:
                plan.append({
                    "type": qtype,
                    "count": count,
                    "difficulty": "medium" # Default for expansion
                })
        return plan

    def expand_pool(self, topic: str) -> bool:
        if not self.try_start_expansion(topic):
            logger.info(f"Expansion already in progress for {topic}")
            return True # Already running
        
        expansion_id = f"exp_{topic}_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        metrics = QuizMetrics(topic=topic)
        context = MetricsContext(quiz_metrics=metrics, topic=topic, expansion_id=expansion_id)

        try:
            decision = self.should_expand_pool(topic)
            if not decision["expand"]:
                return True
                
            self.pool_metrics.record_expansion_attempt()
            start_time = time.perf_counter()
            
            missing = self.calculate_missing_questions(topic)
            plan = self.generate_expansion_plan(topic, missing)
            
            facts = self.retriever.retrieve(topic=topic, limit=20)
            
            total_added = 0
            for task in plan:
                # Need to pass context if generator supports it (Stage 5)
                # For now, just track added
                result = self.generator.generate_questions(
                    topic=topic,
                    count=task["count"],
                    supporting_facts=facts
                )
                
                if result and "questions" in result:
                    for question in result["questions"]:
                        added = self.cache.add_to_pool(
                            topic=topic,
                            subtopic="",
                            difficulty=task.get("difficulty", "medium"),
                            qtype=task["type"],
                            new_questions=[question]
                        )
                        if isinstance(added, int):
                            total_added += added
            
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.pool_metrics.record_expansion_success(expansion_id, topic, total_added, duration_ms)
            return True
        except Exception as e:
            logger.error(f"Expansion failed for topic {topic}: {e}")
            self.pool_metrics.record_expansion_failure(expansion_id, topic, str(e))
            return False
        finally:
            self.finish_expansion(topic)
