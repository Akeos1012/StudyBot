# Architecture Review

This document provides a high-level review of the StudyBot application architecture based on documentation and code structure analysis.

## 1. Current Architecture Strengths

*   **Grounded Generation Pipeline**: The strict separation between data extraction (RAG) and generation (Quiz Pipeline) ensures that the AI's output is rooted in the source knowledge base.
*   **Layered Design**: The application uses a clear orchestration layer (`QuizService`), which decouples API handling from business logic and data processing.
*   **Validation Authority**: The architecture explicitly positions validators as the final authority, effectively creating a "hallucination barrier" around the LLM's output.
*   **Performance Awareness**: Built-in caching mechanisms (`FactCache`, `QuestionCache`) and performance monitoring indicate a proactive design for handling the latency inherent in RAG workflows.

## 2. Current Architecture Weaknesses

*   **High Coupling in `app/quiz`**: The quiz module has grown into a "god module" where `QuizGenerator` depends on nearly every other sub-module in the directory.
*   **Hidden Dependencies**: Heavy inter-importing makes it difficult to trace dependencies, increasing the fragility of the quiz pipeline.
*   **Split Logging Responsibility**: Logging is dispersed across multiple modules, including specialized logging modules and `validation_logger.py`, leading to fragmented monitoring behavior.

## 3. Tight Coupling Areas

*   **`QuizGenerator` (Central Hub)**: This module holds the entire generation pipeline's state and orchestration, making it highly coupled to every sub-component.
*   **Pipeline Inter-dependency**: Many sub-modules in `app/quiz` rely on shared constants or validation helper functions in a way that suggests high coupling (e.g., constants dispersed across modules).

## 4. Separation of Responsibility Problems

*   **Fact Cleaning Logic**: Appears to be duplicated or split between `fact_cleaner.py` and logic embedded directly within `fact_extractor.py`.
*   **Logging**: The proliferation of `validation_logger.py` alongside other logging mechanisms suggests a lack of a unified logging strategy.

## 5. Technical Debt

*   **Circular Dependency Risk**: The dense import graph within `app/quiz` is a significant risk for circular dependencies.
*   **Test/Production Overlap**: The presence of `test_*.py` files within the `app/rag/` directory (if they are being imported in production code) is a structural issue that should be resolved by moving them to a dedicated test directory.

## 6. Performance Bottleneck Risks

*   **Fact Cache Management**: While the `FactCache` optimizes extraction, improper cache invalidation logic could lead to stale data being served or expensive live extractions occurring unexpectedly.
*   **LLM Latency**: The generation process relies on multiple LLM calls per question. As the number of questions requested increases, this pipeline is inherently compute-bound.

## 7. Scalability Concerns

*   **Pool Management**: The simple JSON-based caching mechanism (`question_cache.json`) may not scale to larger note sets or high-frequency usage without moving to a robust database backend.
*   **Memory Usage**: The current design loads large amounts of metadata and facts into memory at startup, which could become problematic if the note set grows significantly.

## 8. Security Risks

*   **Unverified LLM Input**: While grounding validation exists, the pipeline relies on the LLM's output format (`LLMParser`). Ensuring robust sanitization of the JSON output is critical to prevent malformed/malicious input from crashing the pipeline.

## 9. Files/Modules Requiring Caution

*   `app/services/quiz_service.py` (Central orchestrator)
*   `app/quiz/quiz_generator.py` (Central hub)
*   `app/rag/fact_extractor.py` (Knowledge foundation)
*   `app/models/fact_schema.py` / `question_schema.py` (Data contract foundation)

## 10. Recommended Refactoring Priorities

1.  **Decouple `QuizGenerator`**: Break down the generator into smaller, single-responsibility services (e.g., prompt building, distractor selection, question validation) to reduce coupling.
2.  **Unify Logging**: Implement a centralized logging strategy, phasing out fragmented loggers.
3.  **Refactor Directory Structure**: Move test files out of `app/` and into a dedicated `tests/` directory.
4.  **Enforce Schema**: Tighten the use of models in `app/models/` to ensure schema enforcement is strictly applied at module boundaries.
5.  **Clean Fact Extraction**: Consolidate fact cleaning logic into `fact_cleaner.py`.
