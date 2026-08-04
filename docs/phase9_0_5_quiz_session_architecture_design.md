# Quiz Session Backend Architecture Design - Phase 9.0.5

## 1. Current Architecture
The current quiz session management is a simple, JSON-file-based storage (`quiz_sessions.json`) managed by a `SessionManager` singleton. `QuizSession` is a Pydantic model. 
- **Lifecycle**: Sessions are created via `QuizService.create_quiz_session`, and answers are submitted via `QuizService.submit_session_answer` which calls `SessionManager` to update the session state.
- **Limitation**: The current implementation is rudimentary, lacks robust persistence (JSON file is overwritten on every change), lacks structured completion/abandonment tracking, and is tightly coupled with `QuizService` for orchestration.

## 2. Problems Identified
- **Persistence**: File-based storage (`quiz_sessions.json`) is not suitable for concurrent production access or scalability.
- **Statelessness/State loss**: While the `SessionManager` exists, the frontend does not properly leverage this state, often triggering new generations instead of resuming.
- **Analytics/Completeness**: No clear event pipeline for session completion (e.g., scoring at the end of a session).
- **Coupling**: `QuizService` performs too many responsibilities (orchestration, extraction, session management, analytics logging).

## 3. Proposed QuizSession Design
Transition to a more robust `QuizSession` entity and decouple session lifecycle management from `QuizService`.
- **Introduce `QuizSessionService`**: A new service dedicated to session creation, retrieval, and completion.
- **Database Backend**: Migrate from `quiz_sessions.json` to an SQL database (e.g., SQLite or PostgreSQL) to support concurrent read/write and better querying.

## 4. Data Model (`QuizSession` Entity)
Extend `QuizSession` Pydantic model:
- `session_id`: `str` (UUID)
- `user_id`: `str`
- `topic`: `str`
- `difficulty`: `str`
- `question_count`: `int` (Added to track intended length)
- `question_ids`: `List[str]`
- `current_question_index`: `int`
- `status`: `Enum` (ACTIVE, COMPLETED, ABANDONED)
- `created_at`: `datetime`
- `completed_at`: `Optional[datetime]`
- `metadata`: `Optional[Dict[str, Any]]` (For storing scores, session-specific context)

## 5. API Contract
- `POST /quiz/session/create`: Initialize a session.
- `GET /quiz/session/{session_id}`: Fetch session state.
- `POST /quiz/session/{session_id}/answer`: Submit an answer, update session index, log analytics.
- `PATCH /quiz/session/{session_id}/complete`: Explicitly mark session as completed, calculate final score.

## 6. Frontend Integration Requirements
- Frontend must store `session_id` upon creation.
- Frontend should fetch session state on initialization/refresh using `GET /quiz/session/{session_id}` instead of re-calling generate.
- Frontend must call `PATCH .../complete` to finalize the session and show results.

## 7. Migration Strategy
1. **Model Update**: Update `QuizSession` Pydantic model.
2. **Storage Migration**: Create a migration script to map existing JSON data to the new SQL database schema.
3. **API Refactor**: Update `routes.py` to route session management to the new `QuizSessionService`.
4. **Backward Compatibility**: Ensure `quiz_service` can still interact with the new session storage interface.

## 8. Risks
- **Data Loss during Migration**: Mitigate with thorough backup and validation before switching to SQL.
- **API Breaking Changes**: Ensure `POST /quiz/session/create` signature remains stable if possible, or implement a deprecation strategy.
- **Concurrency**: Moving to SQL will require proper handling of session updates to avoid race conditions.

## 9. Final Recommendation
**READY FOR IMPLEMENTATION**
The design resolves the identified bottlenecks and prepares the backend for stateful interaction with the frontend, while providing a clear path for analytics integration.
