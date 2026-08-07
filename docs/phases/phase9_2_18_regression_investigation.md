# Audit Report: Phase 9.2.18 Regression Investigation

## Root Cause
The `POST /quiz/session/create` endpoint is receiving requests without the required `X-User-ID` header. The backend `create_session` route handler retrieves `user_id` from this header:
```python
user_id: Optional[str] = Header(None, alias="X-User-ID")
```
When this header is missing, `user_id` is `None`. This `None` value is passed to `quiz_service.create_quiz_session`, and subsequently to `quiz_session_service.create_session`. Finally, it attempts to instantiate `QuizSession`, which has a mandatory `user_id` field (no `Optional` type), causing a Pydantic `ValidationError`.

## Data Flow Analysis

### Before Phase 9.2.18
The `user_id` was likely not strictly enforced or was passed in a way that didn't reach the Pydantic validator in `QuizSession` when `None`. It's possible earlier versions of `QuizSession` allowed `None` or were not validated as strictly.

### After Phase 9.2.18
The `exclude_ids` integration and associated changes did not *cause* this, but they highlighted a vulnerability in the existing API contract where `user_id` is implicitly required by the `QuizSession` model but not explicitly required by the API route (`Optional[str] = Header(None, ...)`).

## Files Responsible
- `app/api/routes.py`: The `create_session` route handler does not enforce the presence of `X-User-ID`.
- `app/models/quiz_session.py`: The `QuizSession` model expects a mandatory `user_id`.

## Minimal Fix Recommendation
1.  Update the API route in `app/api/routes.py` to make `user_id` mandatory by removing the `Optional` and providing a default or raising a 400 error if missing.
2.  Update `tests/api/test_api.py` to include `headers={"X-User-ID": "test-user"}` in the `requests.post` calls to the `/quiz/session/create` endpoint.

## Regression Risk
Low. This is a fix for an implicit requirement that was previously masked but is now enforced by Pydantic. Ensuring all API calls provide `X-User-ID` is the correct path forward.
