# Step 0 — Implementation Recovery Audit

## Pipeline Mapping
1. **Fact Normalization:** `app/quiz/quiz_generator.py` -> `normalize_fact()`
2. **Question Generation:** `app/quiz/quiz_generator.py` -> `generate_with_retry()` -> `generate_from_fact()` -> `llm.generate()`
3. **Distractor Selection:** `app/quiz/quiz_generator.py` -> `distractor_selector.py`
4. **Validation Pipeline:** `app/quiz/quiz_generator.py` -> `validate_structure()`, `validate_distractors()`, `validate_grounding()`, `validate_question_focus()`, `validate_domain_correctness()`
5. **Caching:** `app/quiz/question_cache.py`
6. **API Layer:** `app/api/routes.py`
7. **Frontend:** `frontend/src/components/QuestionCard.jsx`, `frontend/src/App.jsx`

## Identified Problems
- **Distractor Reliability:** Frequent generation of placeholders ("Distractor 1") when the selector fails.
- **Validation Strictness:** Overly sensitive `grounding` and `focus` validators are causing high rejection rates and low pipeline yield.
- **Pipeline Performance:** Excessive retry attempts due to validation failures.

## Proposed Fixes
1. **Distractor Fix:** Strengthen the `DistractorSelector` logic to ensure that if fallback is required, it pulls related concepts from the fact cache rather than returning generic placeholders.
2. **Validator Adjustment:** Refine `validate_grounding` and `validate_question_focus` to allow for slight linguistic variations, preventing false-negative rejections.
3. **Yield Improvement:** Optimize `generate_with_retry` to use a more effective fallback strategy if initial attempts fail, reducing the need for excessive retries.

---
Status: READY FOR IMPLEMENTATION
