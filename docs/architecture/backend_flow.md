# Backend Execution Flow

This document outlines the execution flow of the StudyBot backend, describing how the application handles requests, generates quizzes, and utilizes internal caches and validation mechanisms.

## 1. Application Startup Flow

The application entry point is `app/main.py`.

1.  **FastAPI Setup**: Initializes the `FastAPI` application instance.
2.  **CORS Middleware**: Configures CORS to allow requests from the frontend.
3.  **Dependency Initialization**:
    *   `MetadataLoader("sample_notes")`: Scans and loads metadata from notes.
    *   `QuizGenerator()`: Prepares the generator, which internally initializes a `FactCache` that pre-loads facts from the notes.
    *   `QuizService(...)`: Instantiates the main service, injecting the `MetadataLoader` and `QuizGenerator`.
4.  **Route Setup**: Calls `setup_routes` from `app/api/routes.py`, passing in the initialized dependencies.
5.  **Router Inclusion**: The generated router is included in the main FastAPI `app`.

## 2. API Request Flow

When an API request (e.g., POST `/quiz/generate`) is received:

1.  **Request Handler**: `app/api/routes.py` handles the HTTP request and extracts parameters (topic, subtopic, count, etc.).
2.  **Service Delegation**: The handler calls the appropriate method in `QuizService` (`app/services/quiz_service.py`), passing the request data.
3.  **Service Processing**: `QuizService` manages the workflow (retrieving notes, extracting/retrieving facts, generating questions).
4.  **Response**: The result from `QuizService` is returned by the handler, potentially raising `HTTPException` on failure.

## 3. Quiz Generation Sequence

The `QuizService.get_or_generate_questions` method coordinates the following sequence:

1.  **Cache Check**: If `fresh=False`, it attempts to retrieve questions from the `QuizGenerator`'s internal `question_cache`.
2.  **Fresh Generation (if needed)**: If no cached questions exist or `fresh=True`:
    *   **Note Retrieval**: Retrieves notes using `MetadataLoader`.
    *   **Fact Preparation**:
        *   Checks `QuizGenerator.fact_cache` for pre-loaded facts.
        *   If missing (cache miss), performs live extraction using `FactExtractor` and grounds facts using `GroundingProcessor`.
    *   **Question Generation**: Uses `QuizGenerator.generate_with_retry` (for multiple choice) and `QuizGenerator.generate_fill_blank` to create questions based on the prepared facts.
    *   **Caching**: Newly generated questions are added to the `question_cache`.
3.  **Shuffle/Format**: The final list of questions is formatted and returned.

## 4. Important Classes and Functions

| Class/Function | Module | Responsibility |
| :--- | :--- | :--- |
| `QuizService` | `app/services/quiz_service.py` | Orchestrates the quiz generation pipeline. |
| `QuizGenerator` | `app/quiz/quiz_generator.py` | Core logic for generating questions. |
| `MetadataLoader` | `app/rag/metadata_loader.py` | Handles loading and querying note metadata. |
| `FactExtractor` | `app/rag/fact_extractor.py` | Extracts facts from markdown content. |
| `GroundingProcessor`| `app/rag/grounding_processor.py`| Grounds extracted facts against source material. |

## 5. Dependencies

*   `main.py` depends on `QuizService`, `MetadataLoader`, `QuizGenerator`, and `routes.py`.
*   `routes.py` depends on `QuizService` and `MetadataLoader` (injected via `setup_routes`).
*   `QuizService` depends on `MetadataLoader`, `FactExtractor`, `GroundingProcessor`, `QuizGenerator`, `QuizMetrics`, and `PerformanceMonitor`.

## 6. Validation and Caching

*   **Caching**:
    *   **Fact Cache**: Managed by `QuizGenerator`, loaded at startup. Used by `QuizService` to avoid live extraction of facts.
    *   **Question Cache**: Managed by `QuizGenerator`, accessed by `QuizService` to serve previously generated questions.
*   **Validation**: Validation is implicitly handled by the `GroundingProcessor` (ensuring facts are grounded) and `QuizGenerator` (which includes validation logic, although not deeply inspected here). `QuizService` coordinates these steps without performing direct validation itself.
