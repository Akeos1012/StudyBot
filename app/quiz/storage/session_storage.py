import sqlite3
import json
from typing import List, Optional, Dict, Any
from app.models.quiz_session import QuizSession, SessionStatus
from datetime import datetime

class QuizSessionStorage:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self._initialize_tables()

    def _initialize_tables(self):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                topic TEXT,
                difficulty TEXT,
                question_count INTEGER,
                question_ids TEXT,
                current_question_index INTEGER,
                status TEXT,
                created_at TIMESTAMP,
                completed_at TIMESTAMP,
                metadata TEXT
            )
        """)
        conn.commit()
        if self.db_manager.db_path != ":memory:":
            conn.close()

    def create_session(self, session: QuizSession):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO quiz_sessions 
            (session_id, user_id, topic, difficulty, question_count, question_ids, current_question_index, status, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session.session_id,
            session.user_id,
            session.topic,
            session.difficulty,
            len(session.question_ids),
            json.dumps(session.question_ids),
            session.current_question_index,
            session.status.value,
            session.created_at,
            json.dumps({}) # metadata
        ))
        conn.commit()
        if self.db_manager.db_path != ":memory:":
            conn.close()

    def get_session(self, session_id: str) -> Optional[QuizSession]:
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM quiz_sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        if self.db_manager.db_path != ":memory:":
            conn.close()
        
        if not row:
            return None
        
        return QuizSession(
            session_id=row["session_id"],
            user_id=row["user_id"],
            topic=row["topic"],
            difficulty=row["difficulty"],
            question_ids=json.loads(row["question_ids"]),
            current_question_index=row["current_question_index"],
            status=SessionStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"],
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None
        )

    def update_session(self, session: QuizSession):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE quiz_sessions 
            SET current_question_index = ?, status = ?, completed_at = ?, metadata = ?
            WHERE session_id = ?
        """, (
            session.current_question_index,
            session.status.value,
            session.completed_at,
            json.dumps(session.model_dump().get("metadata", {})),
            session.session_id
        ))
        conn.commit()
        if self.db_manager.db_path != ":memory:":
            conn.close()
