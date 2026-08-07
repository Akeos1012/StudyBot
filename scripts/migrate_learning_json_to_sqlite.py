import json
import os
import shutil
import sqlite3
import argparse
import sys
from datetime import datetime

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.learning.analytics.db_manager import DBManager

def get_args():
    parser = argparse.ArgumentParser(description="Migrate learning JSON data to SQLite.")
    parser.add_argument("--dry-run", action="store_true", help="Do not write to the database.")
    return parser.parse_args()

def create_backup():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join("backups", f"migration_{timestamp}")
    os.makedirs(backup_dir, exist_ok=True)
    
    files_to_backup = ["mastery_data.json", "learning_history.jsonl"]
    for file in files_to_backup:
        if os.path.exists(file):
            shutil.copy(file, backup_dir)
            print(f"Backed up {file} to {backup_dir}")
    return backup_dir

def run_migration(dry_run):
    args = get_args()
    
    # Initialize
    db_manager = DBManager()
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    stats = {
        "mastery_before": 0, "mastery_after": 0,
        "history_before": 0, "history_after": 0,
        "skipped": 0
    }
    
    try:
        if not args.dry_run:
            cursor.execute("BEGIN")

        # 1. Mastery Migration
        if os.path.exists("mastery_data.json"):
            with open("mastery_data.json", "r") as f:
                data = json.load(f)
            
            users = data.get("users", {})
            for user_id, concepts in users.items():
                for concept, record in concepts.items():
                    stats["mastery_before"] += 1
                    attempts = record.get("attempts", 0)
                    correct = record.get("correct", 0)
                    wrong = attempts - correct
                    mastery = record.get("mastery", 0.0)
                    
                    if not args.dry_run:
                        cursor.execute("""
                            INSERT OR REPLACE INTO mastery_records 
                            (user_id, concept, attempts, correct_count, wrong_count, mastery_score)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (user_id, concept, attempts, correct, wrong, mastery))
                        stats["mastery_after"] += 1

        # 2. History Migration
        if os.path.exists("learning_history.jsonl"):
            with open("learning_history.jsonl", "r") as f:
                for line in f:
                    stats["history_before"] += 1
                    event = json.loads(line)
                    
                    # Idempotency check
                    cursor.execute("""
                        SELECT 1 FROM learning_events 
                        WHERE user_id=? AND session_id=? AND timestamp=?
                    """, (event.get("user_id"), event.get("session_id"), event.get("timestamp")))
                    
                    if cursor.fetchone():
                        stats["skipped"] += 1
                        continue
                        
                    if not args.dry_run:
                        cursor.execute("""
                            INSERT INTO learning_events 
                            (user_id, session_id, event_type, topic, concept, correct, difficulty, response_time_ms, timestamp)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            event.get("user_id"), event.get("session_id"), event.get("event_type"),
                            event.get("topic"), event.get("concept"), event.get("correct"),
                            event.get("difficulty"), event.get("response_time_ms"), event.get("timestamp")
                        ))
                        stats["history_after"] += 1

        if not args.dry_run:
            conn.commit()
            print("Migration committed.")
        else:
            print("Dry run completed - no changes made.")
            
    except Exception as e:
        if not args.dry_run:
            conn.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        conn.close()

    return stats

def main():
    args = get_args()
    
    if not args.dry_run:
        create_backup()
    
    stats = run_migration(args.dry_run)
    
    print("\nPHASE 1.5.12 MIGRATION REPORT")
    print("-" * 30)
    print(f"Before:")
    print(f"  Mastery JSON records: {stats['mastery_before']}")
    print(f"  History JSON events: {stats['history_before']}")
    print(f"After:")
    print(f"  mastery_records rows: {stats['mastery_after'] if not args.dry_run else 'N/A'}")
    print(f"  learning_events rows: {stats['history_after'] if not args.dry_run else 'N/A'}")
    print(f"Skipped/Duplicate records: {stats['skipped']}")
    print(f"Status: SUCCESS")

if __name__ == "__main__":
    main()
