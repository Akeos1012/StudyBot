# Phase 8.2: SQLite Storage Migration Design

## 1. Current Storage Architecture Audit

### Existing Storage
- **`learning_history.jsonl`**: Stores raw quiz attempts as individual JSON objects, one per line.
- **`mastery_data.json`**: A monolithic JSON file containing a nested `users` dictionary mapping to concept records.

### Current Logic
- `app/learning/history_service.py` & `app/learning/history_storage.py`: Handles appending attempts to history.
- `app/learning/mastery_service.py` & `app/learning/mastery_storage.py`: Orchestrates updating mastery records.
- `app/learning/mastery_tracker.py`: Houses the core logic for calculating mastery scores based on `attempts`, `correct`, and `wrong` counts.

### Data Flow
`Quiz Answer` → `History Recording (JSONL)` → `Mastery Update (Tracker)` → `Mastery Storage (JSON)`

---

## 2. Obsidian vs. Analytics Storage Responsibility

It is critical to maintain a clear boundary:

- **Obsidian Vault (Knowledge Source)**: Remains the authoritative source for the *content* used to generate learning materials. It does **not** contain user performance data.
- **SQLite Analytics Database**: Exclusively stores *interaction and performance data* (learning events, progress, mastery history).

**Future Architecture:**
Obsidian (Knowledge) → Preprocessor → Quiz System 
                                         ↓
                              Learning Event Storage (SQLite)
                                         ↓
                              Analytics Service (Aggregation)
                                         ↓
                              API → Frontend Dashboard

---

## 3. SQLite Schema Design Proposal

### `users` table
- `user_id` (TEXT, PRIMARY KEY): Unique identifier for the learner.
- `created_at` (TIMESTAMP): Account creation timestamp.

### `learning_events` table
- `event_id` (INTEGER, PRIMARY KEY): Auto-incrementing ID.
- `user_id` (TEXT, FK): Reference to `users`.
- `session_id` (TEXT): For grouping related events.
- `event_type` (TEXT): 'quiz_submit', 'tutorial_ask'.
- `topic` (TEXT): Related topic.
- `concept` (TEXT): Specific concept tested.
- `correct` (BOOLEAN): Performance result.
- `difficulty` (TEXT): 'easy', 'medium', 'hard'.
- `response_time_ms` (INTEGER, NULLABLE): For engagement metrics.
- `timestamp` (TIMESTAMP): Event occurrence time.

### `mastery_records` table
- `user_id` (TEXT, FK): Reference to `users`.
- `concept` (TEXT): Concept identifier.
- `attempts` (INTEGER): Total attempts.
- `correct_count` (INTEGER): Success count.
- `wrong_count` (INTEGER): Failure count.
- `mastery_score` (REAL): Calculated mastery.
- `recommended_difficulty` (TEXT): Based on mastery.
- `last_updated` (TIMESTAMP): Latest record update time.

---

## 4. Database Index Strategy

To support performant analytics queries, the following indexes are recommended:

1. `(user_id)` on `learning_events`: Essential for all user-specific queries.
2. `(user_id, concept)` on `mastery_records`: Optimizes mastery lookups.
3. `(timestamp)` on `learning_events`: Critical for trend/streak calculations and progress-over-time reports.
4. `(session_id)` on `learning_events`: Speeds up session-based analysis.

---

## 5. Migration Strategy Design

### Extraction
Read `learning_history.jsonl` (streaming/line-by-line) and `mastery_data.json` (load completely).

### Transformation
- **Map Fields**: Map JSON fields to SQLite schema.
- **Handle Missing**:
  - `session_id`: Generate from `timestamp` proximity if missing.
  - `event_type`: Default to 'quiz_submit'.
  - `difficulty`: Calculate from existing `mastery` score.
  - `response_time_ms`: Set to NULL (or placeholder).

### Loading
Use transaction-based batch inserts for performance and atomicity.

---

## 6. Data Verification Strategy

Before shifting application logic, verify the SQLite data:

1. **Count Verification**: Ensure `learning_events` count matches `learning_history` lines.
2. **Aggregation Check**: Compare `SUM(correct_count)` and `SUM(wrong_count)` in SQLite against manually parsed counts from the legacy files.
3. **Score Comparison**: Validate that `mastery_score` in `mastery_records` matches the values calculated from the legacy JSON files.

---

## 7. Rollback Strategy

1. **Backup**: Create a copy of `learning_history.jsonl` and `mastery_data.json` in a `data_backup/` directory.
2. **Failure Handling**: If migration fails or verification fails, the SQLite file is considered compromised. Delete it.
3. **Recovery**: Restore the files from `data_backup/`. The system remains in its original, pre-migration state.

---

## 8. Migration Risks

| Risk | Mitigation |
| :--- | :--- |
| **Data Mismatch** | Extensive ETL unit tests comparing legacy/new data. |
| **Missing History** | Ensure extraction logic handles malformed lines gracefully. |
| **Timestamps** | Normalize all timestamps to ISO-8601 UTC. |

---

## 9. Final Recommendation

- **Readiness**: The architecture design is ready for implementation, provided Phase 8.1 is satisfied.
- **Dependencies**: None, other than the completion of this design.
- **Proceed**: Yes, proceed with implementing the SQLite storage access layer (DAO) as the next step.

