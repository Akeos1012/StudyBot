import pytest
import time
from pathlib import Path
from app.rag.fact_cache import FactCache

# Use a temporary directory for the cache
@pytest.fixture
def cache_dir(tmp_path):
    d = tmp_path / "notes"
    d.mkdir()
    return d

@pytest.fixture
def cache_file(tmp_path):
    return tmp_path / "test_cache.json"

def test_cache_staleness(cache_dir, cache_file):
    # 1. Create a note
    note = cache_dir / "test.md"
    note.write_text("Test Concept - This is a test definition.")
    
    cache = FactCache(notes_path=str(cache_dir), cache_path=str(cache_file))
    
    # Build cache
    cache.build()
    assert len(cache.get_topics()) > 0
    
    # 2. Modify note
    time.sleep(1) # Ensure mtime changes
    note.write_text("Test Concept - This is a modified definition.")
    
    # 3. Load cache (should trigger rebuild due to hash mismatch)
    cache2 = FactCache(notes_path=str(cache_dir), cache_path=str(cache_file))
    facts = cache2.load()
    
    # Verify modification is reflected
    assert facts["default"][0]["definition"] == "Test Concept - This is a modified definition"

def test_cache_unchanged(cache_dir, cache_file):
    # 1. Create a note
    note = cache_dir / "test.md"
    note.write_text("Test Concept - This is a test definition.")
    
    cache = FactCache(notes_path=str(cache_dir), cache_path=str(cache_file))
    cache.build()
    
    # 2. Load again (should be hit)
    cache2 = FactCache(notes_path=str(cache_dir), cache_path=str(cache_file))
    # We can't easily check 'hit' vs 'miss' with this implementation 
    # but we can verify it loads correctly
    facts = cache2.load()
    assert facts["default"][0]["definition"] == "Test Concept - This is a test definition"
