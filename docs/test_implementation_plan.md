# Test Implementation Plan

This document outlines the testing strategy to support the refactoring roadmap, ensuring stability and verification throughout the process.

## 1. Testing Strategy

*   **Pytest Foundation**: Standardize on `pytest` for all testing.
*   **Test-Driven Refactoring**: Before modifying a module, ensure comprehensive unit/integration test coverage exists for its current behavior.
*   **Layered Testing**:
    *   **Unit Tests**: Validate individual classes and functions (`FactExtractor`, `QuestionScorer`, `LLMParser`).
    *   **Integration Tests**: Validate interactions between components (`QuizService` + `RAG`, `QuizGenerator` + `Validator`).
    *   **Regression Tests**: Re-run the full pipeline tests to ensure no functional regressions.

## 2. Test Directory Structure

```text
/tests/
  ├── unit/
  │   ├── rag/             # Fact extraction, caching, metadata
  │   ├── quiz/            # Parsers, validators, scorers, builders
  │   └── utils/           # Data cleaning, normalization
  ├── integration/
  │   ├── pipeline/        # Full RAG -> Quiz generation
  │   └── api/             # API routes + QuizService
  └── conftest.py          # Fixtures (data, mocked LLM responses)
```

## 3. Test Requirements

### Unit Tests
*   `LLMParser`: Robust parsing of valid, malformed, and empty JSON.
*   `QuestionScorer`: Score calculation for schema, semantic, and distractor dimensions.
*   `FactExtractor`: Concept identification and text cleaning.

### Integration Tests
*   `QuizService` + `FactExtractor`: End-to-end fact retrieval.
*   `QuizGenerator` + `QuestionValidator`: Generation-to-validation flow.

### Regression Tests
*   `test_full_pipeline.py`: Must pass before any release.
*   `test_api.py`: Ensure API endpoints remain functional.

## 4. Critical Test Cases

*   **RAG Pipeline**:
    *   Empty notes directory handling.
    *   Frontmatter parsing errors.
    *   MD5 change detection for incremental extraction.
*   **Fact Cache**:
    *   Persistence/Loading of facts.
    *   Invalid JSON/Schema handling.
*   **Quiz Generation**:
    *   Multiple-choice generation logic.
    *   Fill-in-the-blank generation logic.
*   **Validation**:
    *   Grounding validation (fail when not grounded).
    *   Duplicate detection.
*   **Question Cache**:
    *   Pool size capping.
    *   Deduplication logic.
*   **API Flow**:
    *   Request timeout handling.
    *   Invalid parameter rejection.

## 5. Tests Required Before Refactoring

| Module | Required Test Coverage |
| :--- | :--- |
| `quiz_generator.py` | Unit tests for prompt building, distractor logic. |
| `fact_extractor.py` | Unit tests for cleaning and parsing. |
| `quiz_service.py` | Integration tests for full pipeline. |

## 6. Test Execution Order

1.  **Baseline Verification**: Run existing `test_full_pipeline.py` and `test_api.py`.
2.  **Structural Move**: Migrate tests and verify they pass in new location.
3.  **Refactor-Specific Unit Tests**: Write unit tests for the specific module being refactored.
4.  **Integration Suite**: Verify integration between components.
5.  **Final Regression**: Run entire `tests/` suite.
