# Phase 7.5: Source Linker Architecture Audit

This document audits the requirements and design for the `SourceLinker` component in the Personal AI Tutor pipeline.

## 1. Traceability Verification
*   **Metadata Availability**: `RetrievedContext` already contains `facts`, which include `fact_id`, `source`, `concept`, and `topic` for each retrieved fact.
*   **Traceability Logic**: **YES**, `SourceLinker` can generate citations without accessing `FactCache` again because all required traceability data is already encapsulated within the `RetrievedContext` object provided during the retrieval phase.

## 2. Responsibility Verification
*   **Expected Responsibilities**:
    *   Map `RetrievedContext` metadata to the `GeneratedAnswer`.
    *   Construct the final `TutorResponse`.
    *   Maintain strict traceability links.
*   **Forbidden**: Searching notes, generating/inventing facts, calling LLM, or guessing sources.
*   **Architecture Compliance**: The proposed boundary respects these restrictions, acting purely as a transformation layer between context and response.

## 3. Data Contract Verification
*   **Input**: `RetrievedContext` (containing facts + source metadata) AND `GeneratedAnswer` (the raw LLM output).
*   **Output**: `TutorResponse` (containing `answer`, `sources`, `related_concepts`, etc.).
*   **Missing Fields**: None identified; current schemas are robust.

## 4. Source Reliability Rules
*   **Case 1 (Fact exists)**: Return valid source metadata.
*   **Case 2 (No metadata)**: Return `null`/empty for source fields; do not crash.
*   **Case 3 (LLM mentions unknown concept)**: Ignore it; only cite sources linked to `RetrievedContext`.

## 5. Related Concepts Generation
*   **Recommendation**: **(B) RetrievedContext concepts**.
*   **Reasoning**: This adheres to the "no external knowledge" requirement. Concepts should be derived from the validated `RetrievedContext` returned by the `Retriever`.

## 6. Dependency Map
| Component | Status | Responsibility |
| :--- | :--- | :--- |
| `RetrievedContext` | Existing | Passed context metadata. |
| `TutorResponse` | Existing | Final API output structure. |
| `SourceLinker` | New | Citations & traceability binding. |
| `AnswerBuilder` | New | LLM text transformation. |
| `FactCache` | Existing | Source of truth (read-only for linker). |
| `SmartReviewerService` | Existing | Existing pattern for rich feedback. |

## 7. Final Recommendation
**Phase 7.5 readiness: READY FOR IMPLEMENTATION**

**Implementation Location**: `app/tutor/source_linker.py`
**Reasoning**: Centralizes traceability logic, ensuring that citation attachment is consistent across the Tutor service and doesn't leak into the Answer generation or Fact storage layers.
