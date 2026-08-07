# Phase 9.0.3: Quiz Session Architecture Audit

## 1. Current Quiz Generation Flow
- **Generation Point**: `QuizService.get_or_generate_questions`
- **Persistence**: Stateless. Questions are generated or retrieved from cache (`question_cache.py`) and returned to the caller immediately.
- **Session Identification**: There is **no persistent quiz session object** in the backend. The API route (`app/api/routes.py`) receives a request, triggers `QuizService`, and returns the list of questions.
- **Recovery**: Currently impossible. If the frontend refreshes, the state is lost, and the UI must call `/quiz/generate` again, potentially getting a different set of questions if not managed carefully by the client.

## 2. Current Answer Submission Flow
- **Submission Point**: `QuizService.record_answer`
- **Linking**: Answers are linked to questions via `question_id`.
- **Correctness**: Calculated by comparing submitted answer to `question.get("correct")` at the moment of submission.
- **Tracking**: `update_answer_result(question["metadata"], correct)` is called, and learning events are recorded in `AnalyticsRepository`.
- **Session Usage**: The `session_id` in `record_learning_event` defaults to `user_id` if not found in the question metadata, meaning there is currently no true per-quiz session grouping.

## 3. Required Backend Changes (Pre-Phase 9.1)
To support production-ready frontend requirements, the following changes are mandatory:

1.  **Introduce `QuizSession` Model**:
    - `session_id` (UUID), `user_id`, `topic`, `difficulty`, `status` (active, completed), `created_at`.
    - A way to map `question_ids` to the session.
2.  **Update `QuizService`**:
    - Add `create_session(user_id, topic, ...)` method.
    - Update `generate_questions` to associate questions with a valid `session_id`.
    - Update `record_answer` to validate against the `session_id`.
3.  **Refactor API Layer**:
    - Add `POST /quiz/session/create`
    - Add `GET /quiz/session/{id}`
    - Update `POST /quiz/session/{id}/answer`

## 4. Proposed API Contract

### POST /quiz/session/create
- **Request**: `{ "topic": "...", "difficulty": "..." }`
- **Response**: `{ "session_id": "UUID", "questions": [...] }`

### GET /quiz/session/{id}
- **Response**: `{ "session_id": "UUID", "topic": "...", "status": "...", "questions": [...] }`

### POST /quiz/session/{id}/answer
- **Request**: `{ "question_id": "...", "answer": "..." }`
- **Response**: `{ "correct": bool, "explanation": "..." }`

## 5. Final Assessment

- **Current architecture status**: **Insufficient**. Stateless design prevents robust frontend state management, session recovery, or detailed per-session performance analytics.
- **Missing backend pieces**: Persistent `QuizSession` storage, session-linked question generation, API endpoints for session management.
- **Required changes before Phase 9.1**: Implementation of `QuizSession` data model, storage migration, and updated `QuizService` controller logic.
- **Recommended implementation order**: 
    1. Define/Migrate `QuizSession` schema.
    2. Update `QuizService` to handle sessions.
    3. Update `app/api/routes.py` with session endpoints.
    4. Proceed to Phase 9.1 (Frontend Refactor).
