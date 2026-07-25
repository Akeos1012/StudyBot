# StudyBot Project Instructions

## Project Purpose

StudyBot is an AI Study Companion.

It converts Obsidian notes into validated quiz questions.

## Current Architecture

Pipeline:

Obsidian Notes
↓
Note Loader
↓
Preprocessor
↓
Fact Extractor
↓
Fact Cache
↓
Question Builder
↓
Question Validator
↓
API
↓
Frontend

## Core Rules

- AI must never invent answers.
- Facts must come from source notes.
- Validators are the final authority.
- Avoid unnecessary rewrites.
- Modify one module at a time.
- Preserve existing working behavior.

## Development Workflow

Before changing code:

1. Identify affected files.
2. Explain the root cause.
3. Provide a change plan.
4. Make the smallest change.
5. Run tests.
6. Review results.

## Important Areas

Pay attention to:

- Fact extraction
- Question generation
- Question validation
- Cache system
- API flow
- Performance

## Testing

Run tests after changes.

Important tests:

- test_full_pipeline.py
- test_api.py
- test_cache.py
- test_validator.py