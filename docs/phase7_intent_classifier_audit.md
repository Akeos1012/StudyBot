# Phase 7: Intent Classifier V1 Architecture Audit

This document outlines the architecture for the `IntentClassifier`, ensuring deterministic, explainable intent classification for the Personal AI Tutor.

## 1. Current Architecture Findings
*   **Existing Logic**: Preliminary intent detection currently resides within `app/tutor/query_preprocessor.py`. While functional, this creates a violation of single-responsibility principles.
*   **Compatibility**: The `NormalizedQuery` model (in `app/models/tutor_schema.py`) already contains `intent` and `question_style` fields, providing a seamless integration point for an explicit classifier.

## 2. Intent Classification Strategy
**Recommendation: Deterministic Rule-Based Classification**
*   **Reasoning**: Meets all requirements: deterministic, explainable, fast, offline, and zero hallucination risk.
*   **Approach**: Map keywords and patterns to specific intent categories using a prioritized rule set.

## 3. Component Location
*   **Recommendation**: Extract logic from `QueryPreprocessor` and move to `app/tutor/intent_classifier.py`.
*   **Reasoning**: Formalizes the pipeline: `Preprocessor` (text cleaning) -> `IntentClassifier` (intent detection) -> `Retriever` (data acquisition).

## 4. Data Contracts
*   **Input**: `NormalizedQuery` (from `app/models/tutor_schema.py`)
*   **Output**: `Intent` (Enum/str: `EXPLAIN`, `SIMPLIFY`, `COMPARE`, `EXAMPLE`, `QUESTION`, `UNKNOWN`)

## 5. Rule Design Proposal
| Intent | Triggers | Priority |
| :--- | :--- | :--- |
| **COMPARE** | "difference", "vs", "versus", "compare" | High |
| **EXAMPLE** | "example", "show", "give me an example" | High |
| **SIMPLIFY**| "simplify", "simple", "easy", "in plain english"| High |
| **EXPLAIN** | "what is", "tell me about", "explain" | Medium |
| **QUESTION**| "how", "why" (if not covered by others) | Low |

*   **Conflict Handling**: Rules must be evaluated in order of priority (High to Low). A query containing "difference" triggers `COMPARE`, even if it also contains "what is" (EXPLAIN).

## 6. Risks
*   **Ambiguity**: A query like "How to compare RAM and ROM" could trigger both `COMPARE` and `QUESTION`.
    *   *Mitigation*: Prioritize `COMPARE` for any query containing comparison keywords regardless of other triggers.
*   **Coverage**: Unhandled intent types ("UNKNOWN").
    *   *Mitigation*: Default to `UNKNOWN` and have `TutorService` handle this gracefully by prompting the user for clarification.

## 7. Implementation Recommendation
**Phase 7.2 readiness**: **READY FOR IMPLEMENTATION**

**Implementation Location**: `app/tutor/intent_classifier.py`
**Reasoning**: Separation of responsibilities. `IntentClassifier` becomes a reusable, testable component invoked by the `TutorService` pipeline.
