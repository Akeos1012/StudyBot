# Phase 8.3: Analytics Service Design

## 1. Proposed Folder Structure
To cleanly separate concerns, I propose the following structure:
```text
app/
  learning/
    analytics/
      analytics_service.py     # High-level analytics business logic
      analytics_repository.py  # SQLite interaction layer (Queries)
      models.py                # SQL-related data models (DTOs)
    mastery_service.py         # Refactored to use SQLite repository
    # ... legacy files remain untouched ...
```

## 2. Data Flow
1. **Analytics Service (API)** requests data from **Analytics Repository**.
2. **Analytics Repository** executes SQL queries against the **SQLite database**.
3. **Analytics Repository** returns structured DTOs (Data Transfer Objects).
4. **Analytics Service** performs business-level aggregation/calculations.
5. **Analytics Service** returns final insights to the caller.

## 3. Layer Responsibilities

### Analytics Repository
- Owns raw SQL queries for event and mastery data.
- Handles database connections (via a unified manager).
- Maps raw database rows to internal data structures.

### Analytics Service
- Defines business rules (e.g., "what constitutes a weak concept?").
- Orchestrates complex calculations (e.g., "improvement over 30 days").
- Contains no SQL logic.

## 4. Migration Compatibility Strategy
- **Dual-Mode Support**: The `LearningAnalyticsService` will initially be refactored to take a new `repository` argument but will keep optional references to `legacy_storage` to allow for verification or fallback.
- **Verification Mode**: A feature flag (or service mode) will compare results from both legacy JSON files and the new SQLite repository, logging discrepancies if they occur during the transition period.

## 5. Test Plan
- **Repository Tests**: Verify SQL queries return correct rows (using an in-memory SQLite database).
- **Service Unit Tests**: Mock the repository layer to test business logic (e.g., mastery trends, weak detection).
- **Integration Tests**: Verify end-to-end flow from database to analytics output.
- **Accuracy Verification**: Run "Shadow Mode" tests where legacy calculations and new SQL-based calculations are compared on the same historical data.
