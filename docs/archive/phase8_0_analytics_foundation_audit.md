# Phase 8.0: Study Analytics Foundation Audit & Design

## 1. Executive Summary

StudyBot is currently **not ready** for a comprehensive Study Analytics (Mastery Dashboard) feature. While the system possesses foundational logic for tracking individual quiz attempts and calculating concept-level mastery, the current architecture is built on file-based JSON/JSONL storage, which lacks the queryability, aggregation capabilities, and performance necessary to support an analytics dashboard. 

The essential foundational work must include migrating from file-based storage to a relational database (e.g., SQLite), implementing robust event-based logging, and developing an dedicated API layer to serve aggregated analytics data.

---

## 2. Learning Pipeline Trace

The current learning workflow is as follows:

1. **User answers a quiz question**
   - *Responsible*: Frontend (Quiz Panel)
2. **API receives answer**
   - *Responsible File*: `app/api/routes.py`
   - *Function*: `submit_answer`
3. **QuizService processes answer**
   - *Responsible File*: `app/services/quiz_service.py`
   - *Function*: `record_answer`
4. **HistoryStorage records attempt**
   - *Responsible File*: `app/learning/history_service.py` (`record_attempt`)
   - *Storage*: `learning_history.jsonl` (Appends new record)
5. **MasteryService updates mastery**
   - *Responsible File*: `app/learning/mastery_service.py` (`update_mastery`)
   - *Function*: Calls `mastery_tracker.py` to calculate updated mastery based on current performance (`correct` or `incorrect`).
6. **MasteryStorage persists updated mastery**
   - *Responsible File*: `app/learning/mastery_storage.py` (`save_user_records`)
   - *Storage*: `mastery_data.json` (Overwrites the JSON file for the user).

---

## 3. Learning Data Audit

| File | Purpose | Storage Format | Producer | Consumer |
| :--- | :--- | :--- | :--- | :--- |
| `learning_history.jsonl` | Raw quiz attempts | JSONL | `HistoryService` | N/A (un-queried) |
| `mastery_data.json` | Current user mastery | JSON | `MasteryService` | `MasteryService` |

**Limitations**: 
- `learning_history.jsonl` is an append-only log without indices, making time-series analysis or filtered queries (e.g., "attempts per day") prohibitively slow as it grows.
- `mastery_data.json` stores the *current* state. It lacks historical state snapshots, making progress-over-time analysis impossible without reconstructing state from history logs.

---

## 4. Current Analytics Capability Readiness

| Feature | Ready | Partial | Missing | Notes |
| :--- | :---: | :---: | :---: | :--- |
| Overall mastery | X | | | Calculated in `mastery_tracker`. |
| Topic mastery | | X | | Needs aggregation logic. |
| Concept mastery | X | | | Stored per concept. |
| Weak concepts | X | | | Logic exists in `analytics_service`. |
| Weak topics | | X | | Needs aggregation. |
| Progress over time | | | X | Requires time-series storage. |
| Learning streaks | | | X | Requires session tracking. |
| Study sessions | | | X | Requires session tracking. |

---

## 5. Storage Strategy Analysis

The current file-based approach is inappropriate for analytics due to:
- **Lack of Scalability**: Parsing large JSONL files for analytics will slow down the application.
- **Poor Querying**: No capability for complex SQL aggregations (e.g., `GROUP BY topic`).
- **Data Integrity Risks**: Concurrent writes to `mastery_data.json` (a monolithic file) pose a risk of corruption as the user base grows.

---

## 6. Future Analytics Requirements

| Metric | Importance |
| :--- | :--- |
| Mastery Trends | Shows improvement or stagnation over time. |
| Weak Topic Detection | Allows personalized, targeted study sessions. |
| Study Frequency | Motivates consistency and builds study habits. |
| Accuracy Rates | Measures overall question difficulty alignment. |

---

## 7. Proposed Future Architecture

```text
Obsidian (Knowledge) → Preprocessor → Quiz System
                                         ↓
                              Learning Event Storage (SQLite)
                                         ↓
                              Analytics Service (Aggregation)
                                         ↓
                              Analytics API (FastAPI)
                                         ↓
                              Frontend (React Dashboard)
```

**Responsibilities**:
- **SQLite**: Provides transactional integrity and complex SQL queries needed for analytics.
- **Analytics Service**: Aggregates raw events (history) into trend metrics.
- **API**: Serves the frontend with ready-to-render dashboard data.

---

## 8. Migration Readiness

- **Migratable**: Existing raw history in `learning_history.jsonl` and mastery scores in `mastery_data.json` can be parsed and imported into new SQLite tables.
- **Missing**: Session IDs, precise response timestamps (if not already sufficient), and event types (quiz vs. tutorial) must be added in the future.

---

## 9. Risk Analysis

| Risk | Mitigation |
| :--- | :--- |
| Data Loss | Back up JSON/JSONL files before migration. |
| Performance Bottlenecks | Use indexed SQLite tables. |
| Inaccurate Aggregations | Implement thorough testing of the new SQL-based aggregation service. |

---

## 10. Final Recommendations

1. **Current Summary**: System records basic history and current mastery in flat files.
2. **Strengths**: Solid underlying calculation logic.
3. **Weaknesses**: Unscalable storage, missing analytics pipeline.
4. **Required Changes**: Storage migration to SQLite, API expansion, Analytics service enhancement, Dashboard UI development.
5. **Storage Strategy**: SQLite is recommended for a local, single-user desktop application requiring SQL capabilities.
6. **Analytics Readiness**: Low (Foundation missing).
7. **Roadmap**: 
   - 8.1: SQLite Migration
   - 8.2: Analytics API Implementation
   - 8.3: Dashboard UI/Visualization Development
