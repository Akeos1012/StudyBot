import sqlite3
from typing import List, Dict, Any, Optional
from app.learning.analytics.db_manager import DBManager


class AnalyticsRepository:
    def __init__(self, db_manager: DBManager):
        self.db_manager = db_manager

    def get_mastery_records(self, user_id: str) -> List[Dict[str, Any]]:
        conn = self.db_manager.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM mastery_records WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
        if self.db_manager.db_path != ":memory:":
            conn.close()
        return [dict(row) for row in rows]

    def record_learning_event(
        self,
        user_id: str,
        session_id: Optional[str],
        event_type: str,
        topic: Optional[str],
        concept: Optional[str],
        correct: Optional[bool],
        difficulty: Optional[str],
        response_time_ms: Optional[int],
    ) -> None:
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO learning_events (
                user_id,
                session_id,
                event_type,
                topic,
                concept,
                correct,
                difficulty,
                response_time_ms,
                timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                user_id,
                session_id,
                event_type,
                topic,
                concept,
                1 if correct else 0 if correct is not None else None,
                difficulty,
                response_time_ms,
            ),
        )
        conn.commit()
        if self.db_manager.db_path != ":memory:":
            conn.close()

    def get_learning_events(self, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        conn = self.db_manager.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM learning_events 
            WHERE user_id = ? AND timestamp >= date('now', '-' || ? || ' days')
            ORDER BY timestamp DESC
        """,
            (user_id, days),
        )
        rows = cursor.fetchall()
        if self.db_manager.db_path != ":memory:":
            conn.close()
        return [dict(row) for row in rows]

    def get_activity_metrics(self, user_id: str) -> Dict[str, Any]:
        conn = self.db_manager.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total_questions,
                SUM(CASE WHEN correct = 1 THEN 1 ELSE 0 END) as correct_answers,
                COUNT(DISTINCT session_id) as total_sessions,
                COUNT(DISTINCT date(timestamp)) as active_days
            FROM learning_events WHERE user_id = ?
        """,
            (user_id,),
        )
        row = cursor.fetchone()
        if self.db_manager.db_path != ":memory:":
            conn.close()
        return dict(row)

    def upsert_mastery_record(
        self,
        user_id: str,
        concept: str,
        attempts: int,
        correct_count: int,
        wrong_count: int,
        mastery_score: float,
        recommended_difficulty: Optional[str] = None
    ) -> None:
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO mastery_records (
                user_id, concept, attempts, correct_count, wrong_count, 
                mastery_score, recommended_difficulty, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, concept) DO UPDATE SET
                attempts = excluded.attempts,
                correct_count = excluded.correct_count,
                wrong_count = excluded.wrong_count,
                mastery_score = excluded.mastery_score,
                recommended_difficulty = excluded.recommended_difficulty,
                last_updated = CURRENT_TIMESTAMP
            """,
            (user_id, concept, attempts, correct_count, wrong_count, mastery_score, recommended_difficulty),
        )
        conn.commit()
        if self.db_manager.db_path != ":memory:":
            conn.close()
