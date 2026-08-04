# Phase 7.0.6: Personal AI Tutor Contract Definition

This document defines the data contracts and component interfaces required for the Personal AI Tutor.

## 1. NormalizedQuery Contract
Purpose: Converts raw student questions into deterministic retrieval input.

*   `original_question`: str (The exact user input)
*   `normalized_text`: str (Cleaned/normalized query text)
*   `keywords`: List[str] (Extracted searchable terms)
*   `extracted_concepts`: List[str] (Detected concept names)

## 2. Intent Contract
Purpose: Determines user request type.

*   `type`: str (e.g., "EXPLAIN", "COMPARE", "EXAMPLE")

## 3. RetrievedContext Contract
Purpose: Contains validated knowledge retrieved from FactCache for grounding.

*   `found`: bool
*   `facts`: List[Dict[str, Any]] (Validated FactCache entries)
*   `concepts`: List[str]
*   `topics`: List[str]
*   `sources`: List[str] (Obsidian note paths)
*   `supporting_facts`: List[str] (Text used to construct the answer)

## 4. AnswerBuilder Contract
Purpose: Transforms retrieved knowledge into a student-friendly explanation.

*   **Input**: `{"context": RetrievedContext, "intent": Intent, "response_style": "simple | detailed"}`
*   **Output**: `GeneratedAnswer` (string)
*   **Rules**:
    *   **Allowed**: Rewrite retrieved facts, simplify, create examples, format based on intent.
    *   **Forbidden**: Add outside knowledge, fill missing info, create unsupported facts.
*   **Responsibility**: Transformation layer, NOT a knowledge source.

## 5. Source Linker Contract
Purpose: Attach original Obsidian note references to the generated answer.

*   **Input**: `RetrievedContext`, `GeneratedAnswer`
*   **Output**: `TutorResponse` (Source metadata)
*   **Responsibility**: Attach note references; preserve traceability from Answer → Fact → Note.
*   **Rules**: Never invent sources; use only `RetrievedContext` sources; handle missing metadata gracefully.

## 6. TutorResponse Contract
Purpose: Final API learning response.

*   `found`: bool
*   `answer`: str (Grounded explanation)
*   `sources`: List[str]
*   `related_concepts`: List[str]
*   `intent`: str
*   `metadata`: Dict[str, Any]

## 7. Component Flow Diagram
```text
Student Question
        ↓
Query Preprocessor
        ↓
NormalizedQuery
        ↓
+----------------+
|                |
↓                ↓
Intent        Retriever
↓                ↓
Intent      RetrievedContext
        \        /
         \      /
        AnswerBuilder
              ↓
       GeneratedAnswer
              ↓
       Source Linker
              ↓
        TutorResponse
```

## 8. Component Interface Map

| Component | Input | Output | Responsibility |
| :--- | :--- | :--- | :--- |
| **Query Preprocessor** | str (question) | `NormalizedQuery` | Normalize text, extract keywords/concepts. |
| **Intent Classifier** | `NormalizedQuery` | `Intent` | Detect user request type. |
| **Retriever** | `NormalizedQuery` | `RetrievedContext` | Fact lookup in `FactCache`. |
| **Answer Builder** | `RetrievedContext`, `Intent` | `GeneratedAnswer` | Grounded LLM response generation. |
| **Source Linker** | `RetrievedContext`, `Answer` | `TutorResponse` | Link answer to specific source paths. |

## 9. Design Decisions
*   **Separation of Concerns:** Intent classification and Source linking are now distinct, non-mutating steps.
*   **Traceability Chain:** Explicitly established via the Source Linker using the `RetrievedContext` as the ground-truth map.
*   **Transformation vs. Knowledge:** The `AnswerBuilder` is strictly defined as a transformation layer.

## 10. Final Readiness Assessment
Phase 7.0.6 Status: **COMPLETE**
Implementation readiness: **READY FOR PHASE 7.1**

*   Contracts are finalized.
*   Module responsibilities are separated.
*   Data movement between components is defined.
