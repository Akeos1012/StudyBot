# Phase 7.3: FactCache Search Architecture Audit

This document audits the current StudyBot retrieval architecture to prepare for implementing deterministic search capability for the Personal AI Tutor.

## 1. Current Architecture Findings
*   **FactCache (`app/rag/fact_cache.py`)**: Stores facts in a dictionary structure, keyed exclusively by `topic`. Current retrieval is `get_facts(topic)`. It currently lacks search capability and is not indexed for keyword queries.
*   **Retriever (`app/rag/retriever.py`)**: Established orchestration layer. Currently handles filtering and ranking for quiz generation.
*   **Fact Schema (`app/models/fact_schema.py`)**: Rich metadata fields exist (`concept`, `topic`, `definition`/`supporting_fact`, `concept_type`). These are sufficient for deterministic, multi-field keyword and concept matching.

## 2. Search Strategy Decision
**Recommendation: Hybrid Retrieval (Keyword + Concept matching)**
To ensure deterministic, traceable results:
*   **Strategy**: Implement a weighted keyword and concept search within `Retriever`.
*   **Flow**:
    1.  Match exact concepts from `NormalizedQuery.extracted_concepts` (Highest weight).
    2.  Match keywords from `NormalizedQuery.keywords` against `concept`, `topic`, and `definition` fields.
    3.  Filter facts by topic if available in `NormalizedQuery`.
*   **Rejection**: Any query lacking validated matches in `FactCache` must trigger the "not found" fallback.

## 3. Component Responsibility
*   **FactCache**: **Storage-only**. It should NOT implement search logic to maintain single responsibility.
*   **Retriever**: **Search Orchestration**. It is the correct layer to perform ranking, filtering, and cross-topic searching, reusing existing infrastructure developed for quiz generation.

## 4. Data Contracts
*   **Input**: `NormalizedQuery` (from `app/tutor/query_preprocessor.py`)
*   **Output**: `RetrievedContext` (from `app/models/tutor_schema.py`)
*   **Compatibility**: Both schemas are fully compatible with this pipeline.

## 5. Ranking Strategy
**Deterministic Weighted Scoring**:
1.  **Exact Concept Match** (Weight: 10.0)
2.  **Keyword match in `concept` field** (Weight: 5.0)
3.  **Keyword match in `definition` field** (Weight: 2.0)
4.  **Topic match** (Weight: 1.0)

*   **Tie Handling**: Primary sort by score (desc), secondary sort by `weight` (pre-existing field in FactCache).
*   **Limit**: Strict maximum of 10 facts per search.

## 6. Retrieval Quality Rules
*   **Level 1 (Required):** Fact must be grounded in an existing, validated entry in `FactCache`.
*   **Level 2 (Required):** Must provide traceability (Source note path + Fact ID).
*   **Strict Rejection**: Random semantic similarity not backed by keyword or concept overlap is rejected.

## 7. Risks and Mitigations
*   **Risk:** Ambiguous queries returning irrelevant results.
    *   *Mitigation:* Require concept-level matching for higher confidence, return "not found" if score is below a threshold.
*   **Risk:** Performance degradation with large caches.
    *   *Mitigation:* Implement basic keyword indexing (in-memory) within `Retriever` during startup to avoid iterative fact scanning.

## 8. Implementation Recommendation
**Implementation Location**: `app/rag/retriever.py`

**Implementation Plan**:
1.  Extend `Retriever` to implement `search(query: NormalizedQuery) -> RetrievedContext`.
2.  Add a ranking engine within `Retriever` that iterates through facts (or pre-indexed candidates).
3.  Ensure traceability by strictly passing existing source metadata through the `RetrievedContext` container.

**Status: READY FOR IMPLEMENTATION**
