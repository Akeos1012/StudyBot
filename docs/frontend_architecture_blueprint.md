# Frontend Architecture Blueprint

## 1. Design Principles
- Frontend must be purely declarative, consuming backend APIs.
- No business logic in components.
- Standardized loading and error states for all API calls.

## 2. Recommended Page Structure
- **Dashboard**: High-level overview (Analytics).
- **Quiz**: Interactive quiz interface (Backend-managed state).
- **Tutor**: AI conversation interface.

## 3. Page Definitions

### Analytics Dashboard
- **Purpose**: Visualize learning mastery and progress.
- **Required APIs**: `/analytics/mastery`, `/analytics/progress`, `/analytics/weak-topics`.
- **Components**: MasteryChart, WeakTopicsList, ProgressGraph.

### Quiz Interface
- **Purpose**: Execute validated quizzes.
- **Required APIs**: `/quiz/generate`, `/quiz/submit-answer`, `/quiz/review`.
- **State**: `currentQuestion`, `userAnswers`, `isEvaluating`.
