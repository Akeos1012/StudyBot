# Study Analytics Investigation Report

## 1. Executive Summary
The investigation confirms that StudyBot has foundational infrastructure for tracking learning history and mastery at a user level, but lacks integrated analytics services or API endpoints to expose this data. The current data storage (JSON/JSONL) is sufficient for a prototype but would need a more robust database layer for a scalable production-grade dashboard.

## 2. Backend Findings

### Data Sources
- **Learning History**: `app/learning/history_storage.py` (JSONL). Stores individual quiz attempts.
- **Mastery Data**: `app/learning/mastery_storage.py` (JSON). Stores user-level mastery records (e.g., concept-based proficiency).

### Models
- `app/models/user_context.py`: Provides user identification for tracking.
- Various schemas (`api_schema.py`, etc.) support the current quiz flow.

### Services
- `app/learning/history_service.py`: Records attempt data.
- `app/learning/mastery_service.py`: Updates and retrieves mastery scores based on performance.
- `app/learning/analytics_service.py`: Exists but is sparse; intended for analytics processing.

### Database
- **Technology**: File-based (JSON and JSONL).
- **Persistence**: Permanent storage, but lacks querying capabilities needed for complex analytics.

### APIs
- Current APIs focus on generating quizzes and submitting answers.
- **Not Found**: No dedicated analytics or dashboard-specific API endpoints.

### Analytics Readiness
- **Capability**: Partially ready. The backend logic to record attempts and track mastery exists, but it needs an aggregation layer and queryable API.

## 3. Frontend Findings

### Technology
- **Framework**: React 19 (Vite).
- **UI Library**: Tailwind CSS.

### Existing Screens
- Focused on Quiz UI (`QuizPanel.jsx`, `QuestionCard.jsx`) and navigation (`Sidebar.jsx`).
- **Not Found**: No dashboard, progress charts, or statistics pages.

### API Integration
- Communication via standard `fetch` or similar patterns implied within component services.

### UI Components
- Reusable UI elements (`QuestionCard`, `ScoreCard`) exist.
- **Not Found**: No data visualization components (charts, graphs, trends).

### Analytics Readiness
- Not ready. Needs new dashboard layouts and data visualization components.

## 4. Data Availability Assessment

Can StudyBot currently calculate:
- **Topic mastery?**: YES (via `MasteryStorage`)
- **Student progress?**: YES (via `HistoryStorage`)
- **Weak areas?**: PARTIAL (Logic exists, needs aggregation)
- **Learning trends?**: NO (Aggregation/Time-series data lacking)

## 5. Missing Requirements

- **Backend**: Aggregation API endpoints, advanced querying (needs database or indexed store), and a robust Analytics Service.
- **Frontend**: Dashboard layout, chart library, and data visualization components.

## 6. Recommendations Before Planning

1. **Storage Migration**: Transition from file-based JSON to a relational database (e.g., SQLite/PostgreSQL) to support efficient querying for analytics.
2. **Analytics API**: Design REST/GraphQL endpoints for aggregating user progress and mastery data.
3. **Data Aggregation Service**: Enhance `AnalyticsService` to compute time-series data and trends from the raw history logs.
4. **UI Framework**: Choose a chart library (e.g., Recharts) to integrate into the frontend for visualizing mastery and learning progress.
