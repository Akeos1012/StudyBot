# Performance Optimization Plan

This document outlines potential performance bottlenecks in the StudyBot application and provides a plan for optimization.

## 1. Current Performance Bottlenecks

*   **LLM Latency**: The quiz generation pipeline is heavily dependent on LLM calls. Each generation attempt involves an LLM request, which is inherently slow.
*   **Startup I/O**: Initializing `FactCache` and `MetadataLoader` involves scanning and potentially reading a large volume of files from the `sample_notes/` directory.
*   **Memory Footprint**: Loading large dictionaries of metadata and facts into memory at startup may scale poorly as the knowledge base grows.
*   **Redundant Fact Extraction**: If the `FactCache` is not utilized efficiently or misses frequently, expensive live extraction processes are triggered.

## 2. Startup Time Issues

*   **Metadata Indexing**: Scanning the entire `sample_notes/` directory to rebuild the index can be slow.
*   **Fact Cache Building**: Extracting facts from all notes at startup is a heavy I/O and processing operation.

## 3. Runtime Generation Delays

*   **Synchronous LLM Calls**: Generation blocks the request-response cycle.
*   **Validation Overhead**: The multi-stage validation pipeline performs numerous string comparisons and semantic checks for every generated question.
*   **Retry Logic**: While necessary for grounding, the retry mechanism can amplify latency if multiple attempts are needed to generate a valid question.

## 4. Cache Optimization Opportunities

*   **Incremental Fact Extraction**: Instead of rebuilding the entire fact cache, implement incremental updates based on changed file hashes (similar to how `MetadataLoader` detects file changes).
*   **Database Backend**: Transitioning from `facts_cache.json` and `question_cache.json` to a lightweight database (e.g., SQLite) would enable faster queries, improved indexing, and better scalability.

## 5. Memory Optimization Opportunities

*   **Lazy Loading**: Avoid loading full note contents into memory at startup. Load note content only when needed for fact extraction.
*   **Metadata/Fact Paging**: Implement a mechanism to load facts in chunks or by topic as requested, rather than pre-loading everything.

## 6. LLM Call Reduction Strategies

*   **Aggressive Caching**: Ensure the `QuestionCache` is hit effectively before initiating any generation.
*   **Prompt Optimization**: Fine-tune prompts to increase the probability of valid, well-formed JSON output on the first attempt, reducing the reliance on retries.
*   **Batch Generation**: If appropriate for the UI, pre-generate batches of questions for popular topics during off-peak times.

## 7. Safe Optimization Order

1.  **Observability (Highest Priority)**: Before making changes, enhance the existing logging to get precise measurements on which parts of the pipeline take the longest (e.g., I/O vs. LLM vs. validation).
2.  **Incremental I/O**: Implement incremental fact extraction to reduce startup time.
3.  **Lazy Loading**: Implement lazy loading of note content.
4.  **Database Migration**: Consider migrating to a lightweight database if JSON-based scaling limits are hit.
5.  **Concurrency/Async**: Explore making the quiz generation process asynchronous, allowing API requests to return earlier while generation proceeds in the background.
