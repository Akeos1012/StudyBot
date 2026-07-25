# Test Migration Plan

This document outlines the plan to restructure the project's test suite by moving misplaced test files from the `app/` directory to a dedicated `tests/` directory.

## 1. Current Test Locations

*   **Root Directory (`/`)**:
    *   `test_api.py`, `test_cache.py`, `test_full_pipeline.py`, `test_quiz_cache_integration.py`, `test_retriever.py`, `test_validator.py`, `test_explanation_consistency.py`, `test_ollama.py`, `test_quick.py`.
*   **Module Subdirectories (`app/rag/`)**:
    *   `test_cache.py`, `test_extractor.py`, `test_grounding.py`, `test_retriever.py`.

## 2. Proposed New Directory Structure

```text
/tests/
  ├── unit/
  │   ├── rag/             # Moved from app/rag/
  │   ├── quiz/            # New structure
  │   └── utils/           # New structure
  ├── integration/
  │   ├── pipeline/        # Moved from root/
  │   └── api/             # Moved from root/
  └── conftest.py          # Global fixtures
```

## 3. Files to Move

| Current Path | New Destination |
| :--- | :--- |
| `app/rag/test_cache.py` | `tests/unit/rag/test_cache.py` |
| `app/rag/test_extractor.py` | `tests/unit/rag/test_extractor.py` |
| `app/rag/test_grounding.py` | `tests/unit/rag/test_grounding.py` |
| `app/rag/test_retriever.py` | `tests/unit/rag/test_retriever.py` |
| `test_full_pipeline.py` | `tests/integration/pipeline/test_full_pipeline.py` |
| `test_api.py` | `tests/integration/api/test_api.py` |
| *Remaining root `test_*.py`* | Distribute to `tests/integration/` or `tests/unit/` |

## 4. Files to Remain
*   `tests/` (The new directory)

## 5. Import/Path Changes Required

Moving tests into a `tests/` folder at the project root will change the relative import paths for modules under `app/`.

*   **Change**: Any `import` statement in a test file that relies on local sibling imports (if any) or relative paths to `app/` must be updated to absolute imports based on the project root (e.g., `from app.rag import fact_extractor`).
*   **Config**: Ensure `PYTHONPATH` or `pytest` configuration allows imports from the project root.

## 6. Risks During Migration

*   **Broken Imports**: Incorrectly updated import paths will cause test suite failures.
*   **Fixture Scoping**: Fixtures shared across files may need to be moved to `tests/conftest.py` to maintain accessibility.
*   **Path Dependencies**: Some tests might rely on hardcoded paths to `sample_notes/` or other data files that will need updating relative to the new `tests/` file structure.

## 7. Verification Steps After Migration

1.  **Environment Setup**: Ensure the root project directory is in the `PYTHONPATH`.
2.  **Dry Run**: Execute `pytest --collect-only` to verify all tests are discovered.
3.  **Unit Suite**: Run `pytest tests/unit` to verify internal component logic.
4.  **Integration Suite**: Run `pytest tests/integration` to verify workflow integrity.
5.  **Full Suite**: Run `pytest` to ensure 100% pass rate across the entire migrated suite.
