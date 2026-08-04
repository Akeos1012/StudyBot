# Frontend-Backend Integration Audit

## 1. Backend Feature Inventory

| Subsystem | Status | Responsible Files |
| :--- | :--- | :--- |
| **Analytics** | Complete | `app/api/analytics_routes.py`, `app/learning/analytics_service.py` |
| **Quiz Generation** | Complete | `app/api/routes.py`, `app/quiz/quiz_generator.py` |
| **Tutor** | Partial | `app/api/tutor_routes.py`, `app/tutor/` |
| **Knowledge/RAG** | Complete | `app/rag/` |
| **Question Cache** | Complete | `app/quiz/question_cache.py` |

## 2. API Inventory

| Route | Method | Status | Frontend Consumer |
| :--- | :--- | :--- | :--- |
| `/analytics/mastery` | GET | ✓ | AnalyticsDashboard |
| `/analytics/progress` | GET | ✓ | AnalyticsDashboard |
| `/analytics/weak-topics` | GET | ✓ | AnalyticsDashboard |
| `/quiz/generate` | POST | ✓ | App.jsx (Sidebar) |
| `/tutor/ask` | POST | ✗ | None |

## 3. Frontend Inventory

- **Pages:**
    - `AnalyticsDashboard` (Complete, consumes API)
    - `QuizPanel` (Home page, uses internal state instead of full API)
- **Services:**
    - `analyticsApi` (Connected)
    - `api` (Generic API handler)

## 4. Feature Mapping

| Feature | Backend | API | Frontend | Ready |
| :--- | :--- | :--- | :--- | :--- |
| Analytics | AnalyticsService | /analytics/* | AnalyticsDashboard | YES |
| Quiz | QuizService | /quiz/generate | QuizPanel | Partial |
| AI Tutor | TutorService | /tutor/ask | MISSING UI | NO |

## 6. Gap Analysis
- AI Tutor needs full frontend implementation.
- Quiz experience relies on internal React state management; should move to backend-managed sessions.
