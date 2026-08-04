# Phase 8.1: Learning Data Schema Design Report

## 1. Investigation Findings
The current data flow is fragmented:
- **Quiz Answer**: Handled by `QuizService.record_answer` in `app/services/quiz_service.py`.
- **History**: Appended as flat JSON lines in `learning_history.jsonl` by `HistoryStorage`.
- **Mastery**: Stored as a large, complex JSON object in `mastery_data.json` by `MasteryStorage`.
- **Context**: Missing structured session grouping, accurate response time measurements, and event-type differentiation.

## 2. Learning Event Schema Design
To support analytics (mastery trends, weak areas, session activity), a normalized `LearningEvent` schema is recommended.

### Schema Proposal
```json
{
    "event_id": "UUID",
    "user_id": "string",
    "session_id": "UUID",
    "event_type": "enum (quiz_answer, tutor_ask, review_attempt)",
    "topic": "string",
    "concept": "string",
    "correct": boolean,
    "difficulty": "string (easy, medium, hard)",
    "response_time_ms": integer (optional),
    "timestamp": "ISO8601 string"
}
```

### Field Definitions
- **`event_id`**: PK for unique event identification.
- **`user_id`**: Identifier from `UserContext`. Essential for multi-user/persistence.
- **`session_id`**: New requirement. Used to group events within a study session (e.g., one quiz submission = one session).
- **`event_type`**: Enables diverse event tracking (tutor interactions vs. quiz answers).
- **`topic` / `concept`**: Derived from Question metadata.
- **`correct`**: Captured from `QuizService.record_answer`.
- **`difficulty`**: Captured from question metadata.
- **`response_time_ms`**: **Missing**. Requires frontend support to track duration between question load and answer submission.
- **`timestamp`**: Required for trend analysis.

## 3. Analytics Capability Mapping

| Feature | Required Fields | Current Support | Missing Data |
| :--- | :--- | :--- | :--- |
| Overall Mastery | user_id, correct | YES | API Exposure |
| Topic Mastery | user_id, topic, correct | YES | API Aggregation |
| Weak Concepts | user_id, concept, correct | YES | API Querying |
| Progress Trends | timestamp, correct, topic | PARTIAL | Time-series query support |
| Activity History | timestamp, event_type | YES | Proper DB storage |
| Recommendations | concept, difficulty, mastery | YES | Aggregated data |

## 4. Migration Strategy
1. **Schema Initialization**: Create SQLite schema in Phase 8.2.
2. **Backfill**: Parse existing `learning_history.jsonl` and `mastery_data.json` and insert into the `LearningEvent` table.
3. **Dual-write**: (Optional) For a short period, write to both JSON/JSONL and SQLite to validate parity.
4. **Deprecation**: Remove legacy file-based storage only after full validation.

## 5. Final Recommendations
1. **Database Foundation**: SQLite is the recommended storage layer.
2. **Frontend Changes**: Update `api.js` and quiz components to measure and submit `response_time_ms`.
3. **Session Management**: Implement basic session tracking in `QuizService` upon quiz start to group related `quiz_answer` events.
4. **Implementation Risk**: Building analytics directly on the current file-based structure is highly discouraged due to query complexity and performance issues. Foundation (storage migration) must precede implementation.
