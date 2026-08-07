# Phase 8.0: Study Analytics Foundation Audit & Design

## 1. Current Learning Data Pipeline Investigation

### Data Flow
1. **Quiz Submission**: `app/api/routes.py` (`submit_answer` endpoint) receives user input.
2. **Answer Processing**: `app/services/quiz_service.py` (`record_answer`) orchestrates logic.
3. **History Storage**: `app/learning/history_service.py` uses `app/learning/history_storage.py` to append a JSON record to `learning_history.jsonl`.
4. **Mastery Update**: `app/learning/mastery_service.py` (`update_mastery`) calls `app/learning/mastery_tracker.py` to calculate new mastery scores.
5. **Mastery Storage**: Updated mastery records are saved to `mastery_data.json` via `app/learning/mastery_storage.py`.
6. **Analytics Availability**: `app/learning/analytics_service.py` provides read-only methods for statistics but is not currently hooked into the API pipeline.

### Findings
- **Session tracking**: Missing.
- **Timestamps**: Present in history logs (via file append time if not explicitly in JSON, need verification).
- **Difficulty**: Captured in `mastery_tracker.py` as `recommended_difficulty`.
- **Response time**: Missing.

---

## 2. Existing Storage Architecture Audit

### Systems
- **`learning_history.jsonl`**: Stores raw attempts. High analytical value but requires sequential parsing.
- **`mastery_data.json`**: Stores current user state. Low query capability; file-based.

### Analytics Support
- Mastery dashboard: **Partial** (Data exists but needs aggregation).
- Progress trends: **Low** (Hard to query time-series from JSONL).
- Weak topic detection: **Ready** (Logic exists).
- Time-based analysis: **Low** (Expensive parsing required).

---

## 3. Existing Analytics Capability Audit

| Feature | Status | Reason | Missing |
| :--- | :--- | :--- | :--- |
| Overall mastery | READY | Calculated in `mastery_tracker` | API endpoint |
| Topic mastery | PARTIAL | Implicit, needs aggregation | API/Frontend view |
| Weak concepts | READY | Implemented in `analytics_service` | API/Frontend view |
| Improvement trends| MISSING | No time-series aggregation | Logic + Storage |

---

## 4. Data Schema Analysis

### Current Schema (Learning History - JSONL)
```json
{
  "question_id": "...",
  "user_answer": "...",
  "is_correct": bool,
  "timestamp": "..." 
}
```

### Recommended Fields for Analytics
- `session_id`: For grouping events.
- `response_time`: To measure engagement/difficulty.
- `event_type`: (quiz_submit, tutorial_ask).

---

## 5. Obsidian Vault vs Analytics Storage

- **Obsidian**: Remains the **Knowledge Source**.
- **Analytics Storage**: **Separate layer**.
- **Recommendation**: Transition from file-based JSON to **SQLite**. SQLite provides a local, file-based, relational database suitable for StudyBot's "single user/desktop" scope while enabling complex SQL queries required for analytics.

---

## 6. Required Analytics Metrics Design

- **Overview**: Accuracy %, Mastery Score, Total Questions Answered.
- **Topic Analysis**: Topic Mastery Heatmap, Weakest Topics.
- **Progress**: Mastery Trendline (Mastery vs Time), Weekly Engagement Count.
- **Behavior**: Session Length, Study Frequency.

---

## 7. Future Analytics Architecture Proposal

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

---

## 8. Migration Strategy Planning

1. **Storage Setup**: Initialize SQLite schema.
2. **Data Transformation**: Script to parse `learning_history.jsonl` and `mastery_data.json` into SQLite tables.
3. **Validation**: Compare aggregated metrics before/after migration.
4. **Fallback**: Retain old files until full verification.

---

## 9. Frontend Analytics Readiness Audit

- **Framework**: React/Vite (Good).
- **API**: Manual `fetch` (Needs abstraction).
- **Missing**: Charting library (e.g., Recharts), Dashboard layout, Data visualization components.

---

## 10. Final Readiness Assessment

| Component | Status | Missing Work |
| :--- | :--- | :--- |
| Learning History | READY | Migration needed |
| Mastery Calculation | READY | API exposure needed |
| Analytics API | MISSING | New endpoints |
| Dashboard UI | MISSING | Full development |

### Conclusion
1. **Readiness**: Backend (Partial), Storage (Migration needed), API (Missing), Frontend (Missing).
2. **Sequence**: Storage Migration -> Analytics API Implementation -> Frontend Dashboard UI.
3. **Risk**: Implementing analytics on current JSON files will lead to performance bottlenecks and unmaintainable aggregation code. **Foundation (Storage Migration) must come first.**
