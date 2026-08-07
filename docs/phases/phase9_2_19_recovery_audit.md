# Step 0 — Repository Recovery Audit

## Current Status
- **Backend:** Question freshness infrastructure (Phase 9.2.18) is fully implemented and operational. `QuestionCache.sample()`, `QuizService`, and `API routes` are correctly configured to receive `exclude_ids`.
- **Frontend:** Question history tracking and `exclude_ids` propagation are completely missing.
- **API Mismatch:** `frontend/src/services/quiz_api.js` sends `question_count`, while backend expects `count` (based on `QuizRequest`).

## Audit Summary

| Component | Status | Description |
| :--- | :--- | :--- |
| Backend Cache | Working | `QuestionCache.sample()` correctly filters `exclude_ids` |
| Backend API | Working | Route `/quiz/session/create` accepts `exclude_ids` |
| Frontend Tracking | Broken | `App.jsx` does not store `previous_question_ids` |
| Frontend API | Broken | `quiz_api.js` does not send `exclude_ids` |
| API Contract | Broken | Mismatch: `question_count` (sent) vs `count` (expected) |

## Findings
The freshness pipeline is intact on the backend but disconnected on the frontend. The `question_count` vs `count` parameter mismatch also needs to be corrected to ensure compatibility.

---
Final Status: BLOCKED - QUESTION FRESHNESS REGRESSION (Frontend disconnected)
