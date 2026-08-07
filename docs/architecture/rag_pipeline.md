# RAG Pipeline

This document outlines the architecture and functionality of the Retrieval-Augmented Generation (RAG) pipeline in the StudyBot project.

## 1. Purpose of the RAG System

The RAG system is responsible for converting raw, unstructured markdown notes into validated, structured, atomic facts. These facts serve as the ground truth for quiz generation, ensuring the AI companion generates questions rooted in the source material rather than inventing content.

## 2. Input Data Flow

The flow follows this progression:

1.  **Source**: Raw Markdown files in the notes vault.
2.  **Indexing**: `MetadataLoader` scans and indexes files to build metadata (topic, subtopic, file hashes).
3.  **Extraction**: `FactExtractor` cleans and parses note content to identify concepts and definitions.
4.  **Validation**: Concepts are validated, and facts are structured according to a defined schema.
5.  **Caching**: `FactCache` stores the validated facts, allowing the quiz generator to retrieve them without redundant extraction.
6.  **Quiz Generation**: The Quiz Pipeline utilizes these cached/extracted facts to create quiz questions.

## 3. Metadata Loading Process

Managed by `app/rag/metadata_loader.py`:

*   **Discovery**: Recursively finds markdown files in the notes directory.
*   **Parsing**: Reads YAML frontmatter from files to extract `topic` and `subtopic`. Falls back to parent directory name if not specified.
*   **Change Detection**: Maintains a `.file_index.json` containing MD5 hashes of note files. Rebuilds metadata only if files are changed or cache is missing.

## 4. Fact Extraction Process

Managed by `app/rag/fact_extractor.py`:

1.  **Cleaning**: `_sanitize_text` removes markdown formatting, HTML tags, and structural noise.
2.  **Heading Filtering**: `HeadingFilter` identifies and ignores structural/organizational headings that do not contain semantic concept definitions.
3.  **Concept Extraction**: `SemanticConceptExtractor` analyzes lines to identify technical concepts (e.g., "CPU", "Algorithm") using syntactic and semantic patterns.
4.  **Fact Construction**: Atomic facts are built using `create_fact` from the validated concept and its definition, ensuring traceability back to the source note.

## 5. Fact Cache Behavior

Managed by `app/rag/fact_cache.py`:

*   **Building**: Calls `FactExtractor.extract_all()` to traverse all notes and extract facts.
*   **Persistence**: Saves facts into a structured `facts_cache.json` file.
*   **Validation**: Upon loading, `FactCache` runs `validate_cache()` to check facts against the defined schema, removing or normalizing invalid entries.
*   **Access**: Provides `get_facts(topic)` for the Quiz Service to quickly fetch pre-extracted facts.

## 6. Important Classes and Functions

| Class/Function | Module | Responsibility |
| :--- | :--- | :--- |
| `MetadataLoader` | `app/rag/metadata_loader.py` | Indexes markdown files and manages note content. |
| `FactExtractor` | `app/rag/fact_extractor.py` | Parses content into atomic facts. |
| `FactCache` | `app/rag/fact_cache.py` | Manages persistent, validated fact storage. |
| `SemanticConceptExtractor`| `app/rag/fact_extractor.py` | Identifies valid concepts within text lines. |
| `ConceptValidator` | `app/rag/fact_extractor.py` | Enforces rules on what constitutes a valid concept. |

## 7. Validation and Grounding Steps

*   **Semantic Validation**: `ConceptValidator` rejects generic, vague, or sentence-fragment concepts, ensuring only domain-relevant terms are extracted.
*   **Schema Validation**: `FactCache` ensures all facts adhere to the required data structure (`validate_fact`, `normalize_fact`).
*   **Source Grounding**: Every extracted fact maintains a link (`source_note`) to the original markdown file, ensuring questions can always be traced to the source content.

## 8. Dependencies Between Modules

*   `FactCache` depends on `FactExtractor` (for building) and `fact_schema` (for validation).
*   `FactExtractor` depends on `FactCleaner`, `HeadingFilter`, `SemanticConceptExtractor`, `ConceptValidator`, and `fact_schema`.
*   `MetadataLoader` is used independently by the Quiz Service to retrieve note content and structure.
