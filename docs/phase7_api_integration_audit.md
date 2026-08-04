# Phase 7.9: Tutor API Integration Audit

This document outlines the architectural audit for integrating the Personal AI Tutor's `POST /tutor/ask` endpoint.

## 1. Current API Architecture Findings
*   **Structure**: Uses a modular `setup_routes` function in `app/api/routes.py` which returns a FastAPI `APIRouter`. Dependencies are injected at startup in `app/main.py`.
*   **Integration Point**: The new tutor route should be added to `app/api/tutor_routes.py` (a new file), following the existing router registration pattern.

## 2. Request/Response Contract
*   **Request (`TutorAskRequest`)**: Needs a simple Pydantic model with a `question` field (str).
*   **Response (`TutorResponse`)**: The existing `app/models/tutor_response.py` is fully compatible and defines the required schema (`found`, `answer`, `sources`, `related_concepts`, `intent`).

## 3. TutorService Integration Verification
*   **Integration**: The API route will ingest `TutorAskRequest`, pass `question` to `TutorService.ask(question)`, and return the resulting `TutorResponse` object.
*   **Compatibility**: `TutorService.ask()` returns the exactly required `TutorResponse` object. No schema changes are needed.

## 4. Dependency Injection Recommendation
*   **Pattern**: Follow the established pattern: create `TutorService` in `app/main.py` by injecting all required components (`QueryPreprocessor`, `IntentClassifier`, `QueryRetriever`, `AnswerBuilder`, `SourceLinker`, `FallbackHandler`) and pass the `TutorService` to the new tutor router.

## 5. Error Handling Design
*   **Validation**: FastAPI will handle `TutorAskRequest` validation (e.g., missing question).
*   **Service Errors**: `TutorService` already handles internal pipeline errors and returns a safe `TutorResponse` (found=False) rather than raising exceptions, ensuring no stack trace leakage.

## 6. Risks and Mitigations
*   **Risk**: API endpoint attempts retrieval logic directly.
    *   *Mitigation*: Enforce strict routing: `Route` → `TutorService` ONLY.
*   **Risk**: Improper Dependency Injection.
    *   *Mitigation*: Follow the explicit factory pattern established in `app/main.py`.

## 7. Implementation Contract
*   **Route File**: `app/api/tutor_routes.py`
*   **Endpoint**: `POST /tutor/ask`
*   **Request Model**: `class TutorAskRequest(BaseModel): question: str`
*   **Response Model**: `TutorResponse`
*   **Flow**: `Request` -> `API Route` -> `TutorService.ask()` -> `TutorResponse`

**Phase 7.9 Implementation Readiness: READY FOR IMPLEMENTATION**
