# Test Coverage Audit

This audit evaluates the current testing state of the StudyBot application, identifying gaps and establishing testing priorities to support the refactoring roadmap.

## 1. Existing Test Audit

The project currently has a mix of integration tests in the root directory and specialized unit/integration tests located within `app/rag/`.

*   **Root Tests (`/`)**:
    *   `test_api.py`, `test_cache.py`, `test_full_pipeline.py`, `test_quiz_cache_integration.py`, `test_retriever.py`, `test_validator.py`, `test_explanation_consistency.py`, `test_ollama.py`, `test_quick.py`.
    *   *Assessment*: Good coverage for high-level workflows and core components (Cache, Validator, Pipeline).
*   **Module Tests (`app/rag/`)**:
    *   `test_cache.py`, `test_extractor.py`, `test_grounding.py`, `test_retriever.py`.
    *   *Assessment*: Critical RAG component tests. *Issue*: These are structurally misplaced within the `app/` directory.

## 2. Missing Test Coverage Areas

*   **LLM Parsing**: Minimal unit testing for `app/quiz/llm_parser.py`, which is the entry point for unstructured LLM data.
*   **Component Validators**: The quiz validation pipeline consists of multiple steps (structure, distractor, grounding, relevance, etc.), but individual validation components (other than the main `QuestionValidator`) lack granular unit tests.
*   **Scoring Logic**: `app/quiz/question_scorer.py` metrics (schema, semantic, distractor, formatting, readability) need explicit unit tests to ensure weighting changes are predictable.
*   **Performance Baseline**: Lack of automated tests to verify that refactoring does not negatively impact performance metrics established in `docs/performance_baseline.md`.

## 3. Critical Workflows Requiring Tests

*   **Fact Extraction Flow**: End-to-end extraction from raw Markdown to cached atomic facts.
*   **Quiz Generation Flow**: Full pipeline from request to validated, cached question.
*   **LLM-to-Schema Normalization**: `LLMParser` and `QuestionSchema` validation.
*   **Distractor Quality Assurance**: Ensuring `DistractorSelector` produces plausible, non-placeholder options.

## 4. Refactoring Risks Without Tests

*   **Coupling**: Refactoring `QuizGenerator` (high risk) without granular tests for its sub-components (`DistractorSelector`, `PromptBuilder`) is highly likely to break undetected logic.
*   **Logging**: Removing `validation_logger.py` without verifying that error reporting still functions via the new centralized logger.
*   **Fact Cleaning**: Consolidation of fact cleaning logic risks regressions in fact extraction quality if not verified against existing `test_extractor.py`.

## 5. Recommended Test Priority

| Priority | Area | Goal |
| :--- | :--- | :--- |
| **Critical** | RAG/Extraction Logic | Ensure consistency when cleaning/extracting facts during refactoring. |
| **High** | Component-level Validators | Granular tests for structure, grounding, relevance, and ambiguity validators. |
| **High** | LLM Parser | Ensure robust JSON parsing and schema normalization. |
| **Medium** | Scorer Logic | Unit tests for quality scoring metrics. |
| **Low** | Performance Baseline | Automated checks for key performance regressions. |

**Recommended Actions**:
1.  **Structural Move**: Migrate all `test_*.py` files from `app/rag/` to a new top-level `tests/` directory immediately.
2.  **Unitization**: Before refactoring `QuizGenerator`, write unit tests for `PromptBuilder` and `DistractorSelector` to ensure they can be decoupled safely.
