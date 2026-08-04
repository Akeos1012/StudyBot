# Phase 7.4: Query Retriever Implementation - Inspection Report

## 1. Current Data Flow
1. **Raw Question** → `QueryPreprocessor` → `NormalizedQuery` (Cleaned)
2. `NormalizedQuery` → `IntentClassifier` → `TutorIntent` (Intent Identified)
3. `NormalizedQuery` + `TutorIntent` → `Retriever.search()` → `RetrievedContext`

## 2. Existing Responsibilities
*   `QueryPreprocessor`: Text cleaning, noise removal, keyword extraction.
*   `IntentClassifier`: Deterministic intent detection.
*   `Retriever`: Deterministic hybrid search against `FactCache`.

## 3. Retriever.search() Requirement
The `Retriever.search()` implemented in Phase 7.3 *already* handles hybrid retrieval and ranking, fulfilling the core search capability.

## 4. Orchestration Location
`QueryRetriever` should live in `app/tutor/query_retriever.py`. It will serve as the integration layer *after* preprocessing and intent identification are complete.

## 5. Duplication Risks
`QueryRetriever` must purely act as an orchestrator and validator for `Retriever.search()` output. Any ranking, filtering, or scoring logic MUST NOT be duplicated here; it stays within `Retriever.search()`.
