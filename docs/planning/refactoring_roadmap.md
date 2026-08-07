# Refactoring Roadmap

This document provides a prioritized roadmap for refactoring the StudyBot codebase to improve maintainability, reduce coupling, and enhance performance.

## 1. Refactoring Goals

*   **Reduce Coupling**: Break down large, interconnected modules into single-responsibility services.
*   **Improve Maintainability**: Standardize logging, error handling, and file structure.
*   **Enhance Performance**: Implement incremental I/O, lazy loading, and granular monitoring.
*   **Eliminate Technical Debt**: Resolve circular dependencies and clean up structural issues (e.g., test files in `app/`).

## 2. Priority Ranking

| Priority | Focus Area | Goal |
| :--- | :--- | :--- |
| **Critical** | Circular Dependencies & Structural Cleanup | Stabilize codebase, enable safe future changes. |
| **High** | Logging & Observability | Enable precise performance tracking and debugging. |
| **Medium** | Decoupling & Responsibility Separation | Simplify `QuizGenerator` and `QuizService`. |
| **Low** | Performance Optimizations | Implement lazy loading and I/O enhancements. |

## 3. Refactoring Roadmap

### Phase 1: Critical (Stability)
1.  **Move Test Files**: Move `test_*.py` files from `app/` to a dedicated `tests/` directory.
2.  **Resolve Circular Dependencies**: Analyze `app/quiz/` imports and restructure to break dependency cycles, likely by introducing interface modules or moving shared constants.

### Phase 2: High (Observability)
1.  **Unify Logging**: Replace fragmented loggers with a structured, centralized logging system.
2.  **Add Granular Metrics**: Instrument each stage of the validation pipeline and I/O operations to gather baseline timing data.

### Phase 3: Medium (Maintainability)
1.  **Decouple `QuizGenerator`**: Decompose into: `PromptBuilder`, `DistractorSelector`, `ValidationService`, and `QuestionOrchestrator`.
2.  **Consolidate Cleaning Logic**: Centralize all text cleaning and normalization in `app/utils/clean_data.py` (or a similar location) and remove it from `fact_extractor.py` and other modules.

### Phase 4: Low (Performance)
1.  **Incremental I/O**: Refactor `MetadataLoader` and `FactCache` to use incremental updates based on file hashes.
2.  **Lazy Loading**: Implement lazy loading of note content in `FactExtractor`.

## 4. Modules to Refactor First
*   `app/quiz/quiz_generator.py` (Reduce scope/responsibility)
*   `app/rag/fact_extractor.py` (Remove cleaning logic)
*   `app/quiz/validation_logger.py` (Merge into centralized logging)

## 5. Modules NOT to Touch Yet
*   `app/services/quiz_service.py` (Wait until `QuizGenerator` is decoupled)
*   `app/models/fact_schema.py` / `question_schema.py` (High risk, change only after structural issues are resolved)

## 6. Proposed Architecture Improvements
*   **Dependency Injection**: Use explicit DI to pass dependencies instead of module-level imports where possible.
*   **Service Layer**: Strengthen the service layer to act as the sole interface for the quiz pipeline, hiding internal generation complexity.

## 7. Performance-Safe Refactoring Order
1.  Enhance observability (baseline metrics).
2.  Refactor structural debt (circular dependencies).
3.  Decouple logic (reduce complexity).
4.  Implement performance optimizations (incremental I/O, lazy loading).

## 8. Migration Steps
1.  Create feature branch.
2.  Establish baseline metrics for the affected module.
3.  Perform refactor.
4.  Run unit/integration tests.
5.  Verify metrics have not regressed.
6.  Merge to main.

## 9. Testing Requirements
*   **Pre-change**: Ensure all existing tests pass.
*   **Post-change**: Run relevant unit tests for the refactored module and perform integration testing using `test_full_pipeline.py`.
*   **Validation**: Add new test cases to cover the decoupled responsibilities.
