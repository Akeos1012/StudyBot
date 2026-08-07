# StudyBot Project Structure

## Overview

StudyBot is an AI-powered study companion designed to process Obsidian markdown notes, extract factual knowledge, and generate validated quiz questions.

## Directory Structure

```text
C:\Users\Steaven\OneDrive\Desktop\StudyBot\
├───app/                # Main application logic
│   ├───api/            # FastAPI route definitions
│   ├───config/         # Application and quiz configurations
│   ├───models/         # Data schemas (facts, questions, API requests)
│   ├───quiz/           # Question generation, validation, scoring, and optional AI enhancement
│   │   └───monitoring/ # Quiz-specific performance tracking
│   ├───rag/            # Retrieval-Augmented Generation (note loading, extraction)
│   ├───services/       # Orchestration layer (quiz service)
│   └───utils/          # Helper utilities
├───docs/               # Project documentation
├───frontend/           # User interface layer (Vite/React/etc.)
├───sample_notes/       # Obsidian markdown notes (input source)
└───venv/               # Virtual environment (ignored in source control)
```

## Module Responsibilities

### `app/`
Contains the core backend implementation of the AI study companion.

*   **`api/`**: Handles incoming HTTP requests and API route definitions.
*   **`config/`**: Manages configuration settings for the application and quiz generation.
*   **`models/`**: Defines data structures ensuring consistency across the pipeline (e.g., Fact and Question schemas).
*   **`quiz/`**: The core engine for question generation. Responsible for LLM interaction, validation, distractor selection, and question caching.
*   **`rag/`**: Handles Retrieval-Augmented Generation tasks: loading notes, extracting facts, and grounding them.
*   **`services/`**: Contains the `QuizService`, which acts as the orchestrator for the entire quiz generation workflow.
*   **`utils/`**: General-purpose utility scripts, including data cleanup and performance profiling.

### `frontend/`
Contains the frontend application responsible for user interaction and displaying the generated quizzes.

### `sample_notes/`
Serves as the knowledge base for the application, consisting of Markdown files that act as source material for the RAG pipeline.

## Important Files

*   **`app/main.py`**: The main entry point that sets up the FastAPI application.
*   **`app/services/quiz_service.py`**: The central orchestrator that connects the RAG pipeline to the quiz generation engine.
*   **`app/api/routes.py`**: Defines all API endpoints.
*   **`app/rag/fact_extractor.py`**: Handles logic for converting raw note content into structured facts.
*   **`app/quiz/quiz_generator.py`**: The primary module for generating quiz questions from extracted facts.
*   **`app/rag/fact_cache.py`**: Manages cached facts to optimize performance.
*   **`app/quiz/question_cache.py`**: Manages cached quiz questions.
*   **`GEMINI.md`**: Contains project-specific instructions and conventions.
*   **`run.py`**: A helper script to initiate application execution.

## Core Architecture Principle

StudyBot follows a grounded generation pipeline.

Source notes are the authority.

Pipeline:

Notes
↓
Facts
↓
Validation
↓
Questions
↓
Optional AI enhancement

AI must not create unsupported knowledge.