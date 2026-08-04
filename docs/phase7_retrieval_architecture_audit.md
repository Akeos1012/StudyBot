# Phase 7.2: Personal AI Tutor Retrieval Architecture Audit

This document audits the current StudyBot retrieval architecture to determine suitability for the Personal AI Tutor (Phase 7.2).

## 1. Current Architecture Findings
*   **FactCache (`app/rag/fact_cache.py`)**: Authoritative knowledge layer. Provides topic-based lookup via `get_facts(topic)`. Currently lacks search capability.
*   **Retriever (`app/rag/retriever.py`)**: Orchestration layer. Currently handles filtering and ranking for quiz generation.
*   **Fact Schema (`app/models/fact_schema.py`)**: Comprehensive. Includes `concept`, `topic`, `fact_id`, `definition` (as `supporting_fact`), `source`, and `concept_type`. Provides rich, deterministic metadata essential for grounding.
*   **Tutor Schema (`app/models/tutor_schema.py`)**: `NormalizedQuery` and `RetrievedContext` structures align perfectly with the proposed retrieval pipeline.

## 2. Retrieval Strategy Decision (V1)
**Recommendation: Hybrid Retrieval (Keyword + Concept matching)**
Prioritize deterministic, explainable matches.
*   **Priority 1:** Exact concept match (via `NormalizedQuery.extracted_concepts`).
*   **Priority 2:** Keyword matching against `concept`, `definition`, `topic`.
*   **Priority 3:** Same-topic validated facts.
*   **Rejection Criteria:** Random semantic similarity, external knowledge, unsupported inferences.
This approach minimizes hallucination and maximizes traceability.

## 3. Component Responsibilities
| Component | Responsibility |
| :--- | :--- |
| **FactCache** | Authoritative storage/lookup. Should NOT implement search logic. |
| **Retriever** | Orchestrate search across `FactCache` candidates. Apply ranking/filtering. |
| **QueryPreprocessor** | Input normalization (Deterministic input). |
| **TutorService** | Orchestrates flow: `Prep` -> `Retriever` -> `AnswerBuilder`. |

## 4. Data Flow
1.  **Student Question** -> `QueryPreprocessor` -> `NormalizedQuery`.
2.  `NormalizedQuery` -> `Retriever`.
3.  `Retriever` asks `FactCache` for candidates (e.g., specific topic facts).
4.  `Retriever` ranks candidates against `NormalizedQuery` -> `RetrievedContext`.
5.  `RetrievedContext` -> `AnswerBuilder` -> `GeneratedAnswer`.
6.  `GeneratedAnswer` + `RetrievedContext` -> `SourceLinker` -> `TutorResponse`.

## 5. Risks
*   **Semantic Gap:** Users might use synonyms not in `FactCache`. Mitigation: Use `NormalizedQuery.extracted_concepts` to map synonyms to valid concepts if possible.
*   **Weak Ranking:** Basic keyword matching might return poor relevance. Mitigation: Weight exact concept matches significantly higher than keyword matches in `Retriever`.
*   **Over-Retrieval:** Returning too many facts for the LLM. Mitigation: Implement strict `limit` in `Retriever`.

## 6. Implementation Recommendation
**Phase 7.2 readiness:** **READY FOR IMPLEMENTATION**

**Implementation Location:** `app/rag/retriever.py`
**Reasoning:** `Retriever` is already the established orchestration layer for filtering and ranking facts. Extending its responsibility to handle a more refined `query()` method ensures a single entry point for all retrieval needs (Quiz + Tutor), preventing duplicate search logic.
