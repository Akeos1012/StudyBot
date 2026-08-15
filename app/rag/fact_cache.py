import json
from pathlib import Path
from typing import List, Dict, Any
from .cache_utils import get_all_notes_hashes

try:
    from .fact_extractor import FactExtractor
except ImportError:
    from app.rag.fact_extractor import FactExtractor

from ..models.fact_schema import validate_fact, normalize_fact
from .fact_cleaner import clean_facts

CACHE_VERSION = "1.0"

class FactCache:
    def __init__(self, notes_path="sample_notes", cache_path="facts_cache.json"):
        self.notes_path = Path(notes_path)
        self.cache_path = Path(cache_path)
        self.data = {"version": CACHE_VERSION, "hashes": {}, "facts": {}}
        self.extractor = FactExtractor(notes_path)

    def _is_cache_stale(self, current_hashes: Dict[str, str]) -> bool:
        """Check if cache is stale based on version or source note hashes."""
        if self.data.get("version") != CACHE_VERSION:
            return True
        
        cached_hashes = self.data.get("hashes", {})
        if cached_hashes != current_hashes:
            return True
            
        return False

    def validate_fact(self, fact: Dict[str, Any]) -> bool:
        """Validate that a fact has the correct schema using shared schema"""
        return validate_fact(fact)

    def validate_cache(self):
        """Validate all facts in cache and remove invalid ones"""
        removed_count = 0
        normalized_count = 0
        facts = self.data.get("facts", {})

        for topic in list(facts.keys()):
            valid_facts = []
            for f in facts[topic]:
                normalized = normalize_fact(f)
                if normalized and self.validate_fact(normalized):
                    valid_facts.append(normalized)
                    if normalized != f:
                        normalized_count += 1
                else:
                    removed_count += 1
                    concept = f.get("concept", "unknown")
                    print(f"⚠️ Removing invalid fact: {concept}")

            if valid_facts:
                facts[topic] = valid_facts
            else:
                del facts[topic]
                print(f"⚠️ Removing empty topic: {topic}")

        if removed_count > 0 or normalized_count > 0:
            print(f"🗑️ Removed {removed_count} invalid facts, Normalized {normalized_count} facts")
            self.save_cache()
        else:
            print("✅ All facts validated successfully")

        return removed_count

    def build(self):
        print(f"📂 Building fact cache from {self.notes_path}...")
        current_hashes = get_all_notes_hashes(self.notes_path)
        
        # Ensure we look into subdirectories if they represent topics,
        # or treat all md files in notes_path as belonging to a default topic if structured flatly.
        # The current extract_all() implementation iterates over subdirectories.
        raw_facts = self.extractor.extract_all()
        
        # If no facts found, check if it's because extraction is flat or structured
        if not raw_facts:
            # Try flat extraction if no subdirectories found
            print("⚠️ No topics found via subdirectories, checking flat structure...")
            # Simple wrapper to extract from all files in the notes path as 'default' topic
            raw_facts = {"default": self.extractor.extract_facts(
                "".join([open(f, 'r', encoding='utf-8').read() for f in self.notes_path.glob("*.md")]),
                "default"
            )}

        cleaned_facts = {
            topic: clean_facts(facts) for topic, facts in raw_facts.items()
        }

        self.data = {
            "version": CACHE_VERSION,
            "hashes": current_hashes,
            "facts": cleaned_facts
        }

        self.validate_cache()
        self.save_cache()
        return self.data.get("facts", {})

    def save_cache(self):
        """Save cache to disk"""
        try:
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            total_facts = sum(len(v) for v in self.data.get("facts", {}).values())
            print(f"✅ Saved {total_facts} facts to {self.cache_path}")
        except Exception as e:
            print(f"⚠️ Could not save cache: {e}")

    def load(self):
        """Load cache from disk"""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)

                current_hashes = get_all_notes_hashes(self.notes_path)
                if self._is_cache_stale(current_hashes):
                    print("⚠️ Cache is stale or version mismatch, rebuilding...")
                    return self.build()

                print(f"✅ Loaded {sum(len(v) for v in self.data.get('facts', {}).values())} facts from cache")
                self.validate_cache()
                return self.data.get("facts", {})
            except Exception as e:
                print(f"⚠️ Could not load cache: {e}")
                return self.build()
        else:
            print("⚠️ Cache not found, building...")
            return self.build()

    def get_facts(self, topic: str) -> List[Dict[str, Any]]:
        """Get facts for a specific topic"""
        return self.data.get("facts", {}).get(topic, [])

    def get_topics(self) -> List[str]:
        """Get all available topics"""
        return list(self.data.get("facts", {}).keys())

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
