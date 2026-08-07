# Phase 8.4: Analytics API Layer

## Current API Structure
- Routes are organized into `api/routes.py`, `api/tutor_routes.py`, and the newly added `api/analytics_routes.py`.
- FastAPI `TestClient` is used for testing.

## New Endpoints
- `GET /analytics/mastery`: Returns mastery summary (overall, attempts, concepts).
- `GET /analytics/weak-topics`: Returns a list of weak topics based on mastery.
- `GET /analytics/summary`: Returns a combined mastery/progress/weak-topics dashboard overview.

## Data Flow
Frontend → FastAPI Analytics Routes (`analytics_routes.py`) → `LearningAnalyticsService` → `AnalyticsRepository` → SQLite DB.

## Testing Results
- All tests in `tests/api/test_analytics.py` passed.
- Endpoints verified for user header validation and empty data handling.

## Future Frontend Usage
The dashboard can now consume these endpoints to render mastery heatmaps, weak-area lists, and overview metrics.
