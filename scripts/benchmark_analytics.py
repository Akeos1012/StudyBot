import sqlite3
import time
import random
import uuid
from app.learning.analytics.db_manager import DBManager

def benchmark():
    # Setup
    db = DBManager("benchmark.db")
    conn = db.get_connection()
    
    sizes = [10000, 50000, 100000]
    
    for size in sizes:
        print(f"\nBenchmarking with {size} events...")
        # Clear
        conn.execute("DELETE FROM learning_events")
        
        # Populate
        data = [
            ('test_user', str(uuid.uuid4()), 'quiz_submit', 'Database', 'Normalization', random.choice([0, 1]), None, None)
            for _ in range(size)
        ]
        conn.executemany("INSERT INTO learning_events (user_id, session_id, event_type, topic, concept, correct, difficulty, response_time_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", data)
        conn.commit()

        # Measure without index
        start = time.perf_counter()
        conn.execute("SELECT COUNT(*) FROM learning_events WHERE user_id = ?", ('test_user',)).fetchall()
        print(f"Simple Count (no index): {time.perf_counter() - start:.4f}s")

        # Add Index
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_user ON learning_events(user_id)")
        conn.commit()

        # Measure with index
        start = time.perf_counter()
        conn.execute("SELECT COUNT(*) FROM learning_events WHERE user_id = ?", ('test_user',)).fetchall()
        print(f"Simple Count (with index): {time.perf_counter() - start:.4f}s")
if __name__ == "__main__":
    benchmark()
