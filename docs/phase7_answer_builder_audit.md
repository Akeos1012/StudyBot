# Phase 7.6: Answer Builder Architecture Audit

This document audits the architecture for the `AnswerBuilder` component, responsible for transforming retrieved knowledge into student-friendly explanations while strictly adhering to grounding mandates.

## 1. Current Architecture Findings
*   **LLM Client (`app/quiz/llm_client.py`)**: The system has a robust, reusable `LLMClient` that handles interactions with the configured LLM.
*   **Existing Patterns**: The `QuizGenerator` and `SmartReviewerService` provide mature patterns for prompt-based generation. Specifically, `SmartReviewerService` already implements grounded generation where an explanation is constructed from cached facts—this is the closest precedent to the desired `AnswerBuilder` logic.
*   **Grounding Logic**: The pipeline already possesses utilities to validate and normalize factual data before it reaches the generation layer.

## 2. Existing Reusable Components
*   **`app/quiz/llm_client.py`**: Can be used directly to interact with the LLM.
*   **`app/quiz/question_prompt.py`**: The prompt engineering templates within the quiz pipeline can be adapted (though not reused directly) to structure the grounded system prompts.
*   **`app/rag/fact_cache.py`**: Remains the source of truth, read-only for the `AnswerBuilder`.

## 3. AnswerBuilder Responsibility Boundary
*   **Responsibility**:
    *   Convert `RetrievedContext` and `TutorIntent` into natural language.
    *   Adhere to `response_style` (simple vs. detailed).
    *   Format output (tables for `COMPARE`, bullet points for `EXAMPLE`).
*   **Forbidden**:
    *   Adding content, metadata, citations, or concepts not provided in `RetrievedContext`.
    *   Any retrieval or search logic.

## 4. Grounding Strategy
*   **LLM System Prompt**: Mandatory grounding instruction: *"Answer ONLY using the provided facts. If the information is not in the facts, state 'Information unavailable in your knowledge base.' Do not use outside knowledge."*
*   **Content Injection**: Facts must be injected as a distinct context block in the prompt, clearly delimited (e.g., `<context>...</context>`).
*   **Zero-Knowledge Refusal**: If context is empty, the `TutorService` must trigger a fallback response, *preventing* the LLM call entirely.

## 5. Intent Output Contracts
*   **EXPLAIN**: 2-4 sentences, clear.
*   **SIMPLIFY**: 1-2 sentences, beginner-friendly.
*   **COMPARE**: Table format, max 4 rows.
*   **EXAMPLE**: One example only, max 3 sentences, demonstrates retrieved fact content.
*   **QUESTION**: Focus on reasoning based on retrieved context.

## 6. Failure Handling
*   If `RetrievedContext.found` is `False`, the `TutorService` (orchestrator) will intercept and return the fallback message: *"I couldn't find this topic in your knowledge base."*
*   The `AnswerBuilder` should assume it only receives valid, non-empty contexts.

## 7. Risks and Mitigations
*   **Hallucination**: LLM might try to augment explanations with external training knowledge.
    *   *Mitigation*: Rigid system prompt + pre-LLM context verification + post-generation check (future scope).
*   **Format Breaking**: LLM might provide a paragraph instead of a table for `COMPARE` intent.
    *   *Mitigation*: Strict format instructions and examples in the prompt templates.

## 8. Implementation Recommendation
*   **Recommended Location**: `app/tutor/answer_builder.py`
*   **Recommended Dependencies**:
    *   `LLMClient` (`app/quiz/llm_client.py`)
    *   `TutorPromptTemplates` (to be created in `app/tutor/prompts.py`)
    *   `RetrievedContext` (Data input)
*   **Implementation Order**:
    1. Define prompt templates (`app/tutor/prompts.py`).
    2. Implement `AnswerBuilder` logic using the `LLMClient`.
    3. Integration testing with `TutorService` (to be created next).

**Status: READY FOR IMPLEMENTATION**
