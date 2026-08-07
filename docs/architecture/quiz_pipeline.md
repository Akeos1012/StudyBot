# Quiz Generation Pipeline

This document outlines the architecture and functionality of the quiz generation pipeline in the StudyBot project, which transforms extracted facts into validated quiz questions.

## 1. Purpose of the Quiz Pipeline

The quiz pipeline is responsible for converting raw, trusted facts (extracted from notes by the RAG pipeline) into structured, validated quiz questions (multiple-choice or fill-in-the-blank).

**Core Principle**: The LLM is strictly used for linguistic transformation (rephrasing facts into questions) and **must never invent facts or answers**. Validation is the final authority to ensure accuracy and groundedness.

## 2. Question Generation Flow

1.  **Fact Selection**: `QuizGenerator` retrieves relevant facts for the topic.
2.  **Prompt Building**: `QuestionPrompt` constructs a prompt instructing the LLM to generate questions *only* based on the provided fact.
3.  **LLM Generation**: The LLM generates the question content.
4.  **Parsing**: `LLMParser` extracts and normalizes the JSON output.
5.  **Validation**: A multi-stage pipeline validates the question's structure, grounding, and quality.
6.  **Caching**: Validated questions are stored in `QuestionCache`.

## 3. Multiple Choice Generation Flow

1.  Fact + Answer are passed to the prompt builder.
2.  LLM generates the question text and explanation.
3.  `DistractorSelector` generates 3 incorrect distractors based on the concept type.
4.  Options are shuffled and normalized.
5.  Validation pipeline checks for grounding, relevance, and quality.

## 4. Fill-in-the-Blank Generation Flow

1.  Handled by `FillBlankGenerator` (delegated from `QuizGenerator`).
2.  Fact is analyzed to create a sentence with a blank (`_______`) instead of the concept.
3.  Validation ensures the answer is not already revealed in the sentence.

## 5. Validation Pipeline

The `QuizGenerator` enforces a strict validation order before accepting a question:

1.  **Structure**: Required fields, option count, formatting.
2.  **Distractors**: Rejects placeholder/generic distractors.
3.  **Grounding**: Verifies the question and answer are explicitly supported by the source fact.
4.  **Relevance**: Ensures the question maps to the requested topic.
5.  **Ambiguity**: Rejects questions where distractors might be correct or are mentioned in the question.
6.  **Semantic**: Ensures the question phrasing is coherent.
7.  **Domain**: Checks for factual domain correctness.
8.  **Quality Score**: `QuestionScorer` evaluates overall quality.

## 6. Scoring System

`QuestionScorer` evaluates questions based on:

*   **Schema (25%)**: Structural validity.
*   **Semantic (30%)**: Coherence between question, answer, and explanation.
*   **Distractors (25%)**: Uniqueness and plausibility of distractors.
*   **Formatting (10%)**: Consistency of options.
*   **Readability (10%)**: Clarity and length constraints.

A question must meet a minimum score threshold (defined in settings) to be accepted.

## 7. Cache Behavior

Managed by `QuestionCache` (`app/quiz/question_cache.py`):

*   **Storage**: Questions are stored in pools keyed by topic, subtopic, difficulty, and type.
*   **Persistence**: Saved to `question_cache.json`.
*   **Retrieval**: Provides sampled questions. If the pool is depleted, it triggers the LLM generation flow.
*   **Deduplication**: Uses `QuestionSimilarity` to prevent similar questions from entering the pool.

## 8. LLM Usage Boundaries

*   **Transformation ONLY**: The LLM acts as a rephraser, not a knowledge source.
*   **Fact Grounding**: Every prompt is restricted to specific facts. If the fact does not support the answer, validation will reject the output.
*   **No Invention**: If the LLM invents information, the validation pipeline (specifically Grounding and Domain validation) is designed to reject the question.

## 9. Important Classes and Functions

| Class/Function | Module | Responsibility |
| :--- | :--- | :--- |
| `QuizGenerator` | `app/quiz/quiz_generator.py` | Orchestrates the entire generation pipeline. |
| `QuestionValidator` | `app/quiz/question_validator.py` | Authority for question validation (rejects invalid). |
| `QuestionCache` | `app/quiz/question_cache.py` | Manages persistent storage of validated questions. |
| `QuestionScorer` | `app/quiz/question_scorer.py` | Evaluates question quality. |
| `LLMParser` | `app/quiz/llm_parser.py` | Normalizes LLM JSON output. |

## 10. Dependencies

*   `QuizGenerator` depends on `QuestionCache`, `QuestionScorer`, `QuestionValidator`, `LLMParser`, `DistractorSelector`, and the RAG `FactCache`.
*   `QuestionValidator` depends on `options_parser` and `question_schema`.
*   `QuestionCache` depends on `QuestionValidator` and `QuestionSimilarity`.
