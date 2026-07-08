import json
import hashlib
import random
from difflib import SequenceMatcher
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

class QuestionCache:
    def __init__(self, cache_file="question_cache.json", pool_size=30):
        self.cache_file = Path(cache_file)
        self.cache = {}
        self.pool_size = pool_size
        self.load_cache()
    
    def load_cache(self):
        """Load cache from disk"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                print(f"✅ Loaded {sum(len(v) for v in self.cache.values())} cached questions across {len(self.cache)} pools")
            except Exception as e:
                print(f"⚠️ Could not load cache: {e}")
                self.cache = {}
        else:
            self.cache = {}
    
    def save_cache(self):
        """Save cache to disk"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved {sum(len(v) for v in self.cache.values())} questions across {len(self.cache)} pools")
        except Exception as e:
            print(f"⚠️ Could not save cache: {e}")
    
    def get_key(self, topic: str, subtopic: str = "", difficulty: str = "medium", qtype: str = "multiple") -> str:
        """Generate cache key from parameters"""
        key_str = f"{topic}_{subtopic}_{difficulty}_{qtype}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _is_invalid_cached_question(self, question: Dict[str, Any]) -> bool:
        """Reject cached questions that are fallback-only, lack grounding, or have mismatched explanations."""
        if not isinstance(question, dict):
            return True
        if question.get('_is_fallback', False):
            return True
        if not question.get('explanation'):
            return True
        if not question.get('supporting_fact'):
            return True
        if not question.get('source_note') or not question.get('fact_id'):
            return True
        supporting_fact = str(question.get('supporting_fact', ''))
        if '#' in supporting_fact or '[[' in supporting_fact or ']]' in supporting_fact or '---' in supporting_fact:
            return True
        if len(supporting_fact.split()) > 24:
            return True
        if len(question.get('explanation', '').split()) > 24:
            return True
        try:
            from .quiz_generator import explanation_contradicts_answer
            return explanation_contradicts_answer(question)
        except Exception as e:
            print(f"⚠️ Could not validate cached question: {e}")
            return False

    def get_pool(self, topic: str, subtopic: str = "", difficulty: str = "medium", qtype: str = "multiple") -> List[Dict[str, Any]]:
        """Get the full stored pool for this topic"""
        key = self.get_key(topic, subtopic, difficulty, qtype)
        pool = self.cache.get(key, [])
        valid_pool = [q for q in pool if not self._is_invalid_cached_question(q)]
        if len(valid_pool) != len(pool):
            self.cache[key] = valid_pool
            self.save_cache()
            print(f"🧹 Removed {len(pool) - len(valid_pool)} invalid cached questions for {topic}")
        return valid_pool
    
    def _answer_text(self, q: Dict[str, Any]) -> str:
        """Extract the correct answer text from a question"""
        correct = q.get('correct', '')
        for opt in q.get('options', []):
            if opt.startswith(f"{correct})"):
                return opt.split(')', 1)[-1].strip().lower()
        return ""
    
    def _is_similar_to_pool(self, question: Dict[str, Any], pool: List[Dict[str, Any]], threshold: float = 0.6) -> bool:
        """Check if a question is too similar to existing questions in the pool"""
        q_text = question.get('question', '')
        q_words = set(q_text.lower().split())
        
        for existing in pool:
            existing_text = existing.get('question', '')
            # Check word overlap
            existing_words = set(existing_text.lower().split())
            overlap = len(q_words.intersection(existing_words))
            min_len = min(len(q_words), len(existing_words))
            if min_len > 0 and overlap / min_len > 0.5:
                return True
            # Check ratio
            ratio = SequenceMatcher(None, q_text.lower(), existing_text.lower()).ratio()
            if ratio > threshold:
                return True
        return False
    
    def add_to_pool(self, topic: str, subtopic: str, difficulty: str, qtype: str, new_questions: List[Dict[str, Any]]):
        """Add new questions to the pool, deduping by answer text AND text similarity"""
        key = self.get_key(topic, subtopic, difficulty, qtype)
        existing = self.cache.get(key, [])
        seen_answers = {self._answer_text(q) for q in existing}
        
        added_count = 0
        for q in new_questions:
            # Skip fallback questions
            if q.get('_is_fallback', False):
                print(f"⚠️ Skipping fallback question: {q.get('question', '')[:40]}...")
                continue
            
            ans = self._answer_text(q)
            if ans and ans in seen_answers:
                print(f"⚠️ Skipping duplicate answer: '{ans}'")
                continue
            
            # Check text similarity against entire pool
            if self._is_similar_to_pool(q, existing):
                print(f"⚠️ Skipping text-similar question: '{q.get('question', '')[:40]}...'")
                continue
            
            existing.append(q)
            seen_answers.add(ans)
            added_count += 1
        
        # Cap pool size to prevent unbounded growth
        if len(existing) > self.pool_size * 2:
            # Keep the most recent questions (by preserving order)
            existing = existing[-self.pool_size * 2:]
        
        self.cache[key] = existing
        self.save_cache()
        if added_count > 0:
            print(f"➕ Added {added_count} new questions to pool for {topic} (pool size: {len(existing)})")
        else:
            print(f"⚠️ No new questions added to pool for {topic} (pool size: {len(existing)})")
    
    def sample(self, topic: str, subtopic: str = "", difficulty: str = "medium", qtype: str = "multiple", count: int = 3) -> Optional[List[Dict[str, Any]]]:
        """Randomly sample questions from the pool"""
        pool = self.get_pool(topic, subtopic, difficulty, qtype)
        if len(pool) < count:
            return None  # pool too small, caller should generate more
        return random.sample(pool, count)
    
    def get_pool_size(self, topic: str, subtopic: str = "", difficulty: str = "medium", qtype: str = "multiple") -> int:
        """Get the current pool size"""
        return len(self.get_pool(topic, subtopic, difficulty, qtype))
    
    def clear(self):
        """Clear all cache"""
        self.cache = {}
        self.save_cache()
        print("🗑️ All cache cleared")
    
    def invalidate_topic_cache(self, topic: str, subtopic: str = "", difficulty: str = "medium", qtype: str = "multiple"):
        """Safely clear a specific topic pool without touching unrelated caches."""
        self.clear_topic(topic, subtopic, difficulty, qtype)

    def clear_topic(self, topic: str, subtopic: str = "", difficulty: str = "medium", qtype: str = "multiple"):
        """Clear cache for a specific topic using exact key matching"""
        key = self.get_key(topic, subtopic, difficulty, qtype)
        if key in self.cache:
            del self.cache[key]
            self.save_cache()
            print(f"🗑️ Cleared pool for topic: {topic} (subtopic: {subtopic}, difficulty: {difficulty}, type: {qtype})")
        else:
            print(f"⚠️ No pool found for topic: {topic} (key may not match — check subtopic/difficulty/qtype params)")
    
    def get_pool_summary(self, topic: str = None) -> Dict[str, Any]:
        """Get a summary of the pool for debugging"""
        if topic:
            key = self.get_key(topic, "", "medium", "multiple")
            pool = self.cache.get(key, [])
            return {
                "topic": topic,
                "pool_size": len(pool),
                "questions": [q.get('question', '')[:50] + '...' for q in pool[:5]]
            }
        else:
            return {
                "total_pools": len(self.cache),
                "total_questions": sum(len(v) for v in self.cache.values())
            }