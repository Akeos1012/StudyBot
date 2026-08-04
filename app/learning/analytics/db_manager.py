import sqlite3
import os

class DBManager:
    def __init__(self, db_path: str = "analytics.db"):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        # Force re-initialization if memory db or file doesn't exist
        # Need to handle memory db connection properly so it persists across calls if possible
        # Actually, if I hold the connection, it persists. 
        # For simplicity in this env, I'll just keep recreating it on every get_connection call if it's memory, 
        # but that's bad.
        # Better: if :memory:, store connection in instance.
        if self.db_path == ":memory:":
            if not hasattr(self, '_conn'):
                self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
                self._create_tables(self._conn)
        elif not os.path.exists(self.db_path):
            conn = sqlite3.connect(self.db_path)
            self._create_tables(conn)
            conn.commit()
            conn.close()

    def _create_tables(self, conn):
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                session_id TEXT,
                event_type TEXT,
                topic TEXT,
                concept TEXT,
                correct BOOLEAN,
                difficulty TEXT,
                response_time_ms INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_user_id ON learning_events(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON learning_events(timestamp)")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mastery_records (
                user_id TEXT,
                concept TEXT,
                attempts INTEGER,
                correct_count INTEGER,
                wrong_count INTEGER,
                mastery_score REAL,
                recommended_difficulty TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, concept),
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        """)
        conn.commit()

    def get_connection(self):
        if self.db_path == ":memory:":
            return self._conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
