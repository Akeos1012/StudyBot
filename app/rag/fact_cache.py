import json
from pathlib import Path
from typing import List, Dict, Any

try:
    from .fact_extractor import FactExtractor
except ImportError:
    from app.rag.fact_extractor import FactExtractor

from ..models.fact_schema import validate_fact, normalize_fact

class FactCache:
    def __init__(self, notes_path="sample_notes", cache_path="facts_cache.json"):
        self.notes_path = Path(notes_path)
        self.cache_path = Path(cache_path)
        self.cache = {}
        self.extractor = FactExtractor(notes_path)
    
    def validate_fact(self, fact: Dict[str, Any]) -> bool:
        """Validate that a fact has the correct schema using shared schema"""
        return validate_fact(fact)
    
    def validate_cache(self):
        """Validate all facts in cache and remove invalid ones"""
        removed_count = 0
        normalized_count = 0
        
        for topic in list(self.cache.keys()):
            valid_facts = []
            for f in self.cache[topic]:
                # First try to normalize the fact
                normalized = normalize_fact(f)
                if normalized:
                    # Validate the normalized fact
                    if self.validate_fact(normalized):
                        valid_facts.append(normalized)
                        if normalized != f:
                            normalized_count += 1
                    else:
                        removed_count += 1
                        concept = f.get('concept', 'unknown')
                        print(f"⚠️ Removing invalid fact after normalization: {concept}")
                else:
                    removed_count += 1
                    concept = f.get('concept', 'unknown')
                    print(f"⚠️ Removing fact that couldn't be normalized: {concept}")
            
            if valid_facts:
                self.cache[topic] = valid_facts
            else:
                del self.cache[topic]
                print(f"⚠️ Removing empty topic: {topic}")
        
        if removed_count > 0 or normalized_count > 0:
            print(f"🗑️ Removed {removed_count} invalid facts")
            print(f"🔄 Normalized {normalized_count} facts")
            self.save_cache()
        else:
            print("✅ All facts validated successfully")
        
        return removed_count
    
    def build(self):
        """Build cache from all notes"""
        print("📂 Building fact cache...")
        self.cache = self.extractor.extract_all()
        
        # Validate and normalize after building
        self.validate_cache()
        
        # Save to disk
        self.save_cache()
        
        return self.cache
    
    def save_cache(self):
        """Save cache to disk"""
        try:
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
            total_facts = sum(len(v) for v in self.cache.values())
            print(f"✅ Saved {total_facts} facts to {self.cache_path}")
        except Exception as e:
            print(f"⚠️ Could not save cache: {e}")
    
    def load(self):
        """Load cache from disk"""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                
                total_facts = sum(len(v) for v in self.cache.values())
                print(f"✅ Loaded {total_facts} facts from cache")
                
                # Validate and normalize after loading
                self.validate_cache()
                
                return self.cache
            except Exception as e:
                print(f"⚠️ Could not load cache: {e}")
                return self.build()
        else:
            print("⚠️ Cache not found, building...")
            return self.build()
    
    def get_facts(self, topic: str) -> List[Dict[str, Any]]:
        """Get facts for a specific topic"""
        return self.cache.get(topic, [])
    
    def get_topics(self) -> List[str]:
        """Get all available topics"""
        return list(self.cache.keys())
    
    def refresh(self):
        """Rebuild the cache"""
        return self.build()

if __name__ == "__main__":
    # Test the cache
    cache = FactCache()
    cache.build()
    
    print(f"\n📊 Available topics: {cache.get_topics()}")
    
    # Show sample facts
    for topic in cache.get_topics()[:3]:
        facts = cache.get_facts(topic)
        print(f"\n{topic}: {len(facts)} facts")
        for f in facts[:2]:
            print(f"  - {f['concept']}: {f['definition'][:50]}...")