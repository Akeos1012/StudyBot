# Frontend Quiz Refactor Audit - Phase 9.1

## 1. Current Frontend Limitations
- **Stateless Quiz**: The current `App.jsx` handles quiz generation and answer submission as a stateless flow (`generateQuiz` makes a single API call for questions, and state is lost on refresh).
- **Business Logic in Component**: `App.jsx` contains quiz logic (`calculateScore`, `selectAnswer`, `extractLetter`), making it difficult to maintain and extend.
- **API Coupling**: `App.jsx` directly calls the service layer (`api.generateQuiz`).

## 2. Proposed Architecture
- **Service Layer (`frontend/src/services/quiz_api.js`)**: Encapsulates all backend session API interactions (`POST /create`, `GET /session`, `POST /answer`, `PATCH /complete`).
- **Hook Layer (`frontend/src/hooks/useQuizSession.js`)**: Manages quiz state (loading, session info, answer state, progress) and coordinates with the service layer.
- **Component Layer (`frontend/src/pages/quiz/`)**:
    - `QuizPage`: Top-level component orchestrating the quiz flow using `useQuizSession`.
    - `QuestionCard`: UI for displaying a single question.
    - `QuizProgress`: UI for tracking progress (answered/total).
    - `CompletionSummary`: UI for displaying final results after `completeSession`.

## 3. Implementation Plan
1. **Create Service**: Implement `quiz_api.js` for API communication.
2. **Create Hook**: Implement `useQuizSession.js` to manage session lifecycle state.
3. **Build Pages/Components**: Create `frontend/src/pages/quiz/` with the required components.
4. **Refactor `App.jsx`**: Migrate routing to use `QuizPage` and remove quiz-related state.
5. **Verify**: Ensure the UI correctly uses `session_id` and restores state on refresh.

## 4. Final Recommendation
**READY FOR IMPLEMENTATION**
The design will allow for a robust, persistent quiz experience that aligns with the backend architecture implemented in Phase 9.0.6/9.0.7.
