# Performance Baseline Report

This report summarizes the current performance monitoring infrastructure and establishes a baseline for future optimizations in the StudyBot pipeline.

## 1. Current Measurable Pipeline Stages

The backend currently tracks performance for the following key stages via `QuizMetrics` and `PerformanceMonitor`:

*   **Note Retrieval**: Measured in `QuizService.generate_questions_for_topic` (Note retrieval stage).
*   **Fact Extraction**: Measured in `QuizService.generate_questions_for_topic` (Fact extraction stage).
*   **Question Generation**: Measured in `QuizService.generate_questions_for_topic` (Question generation stage).
*   **LLM Generation**: Time taken per LLM call (`llm_time`, `llm_call_times`).
*   **Total Generation**: End-to-end time (`generation_time`).

## 2. Existing Metrics Collection

The infrastructure relies on two primary components:

*   **`QuizMetrics`**: Tracks pipeline progress (notes loaded, facts extracted), question counts (requested, generated, accepted, rejected), LLM usage (calls, time, retries), and hardware performance (CPU, RAM, GPU utilization/temperature).
*   **`PerformanceMonitor`**: A decorator/wrapper approach that uses `psutil` and `nvidia-smi` to snapshot hardware state at the beginning and end of the generation process.

## 3. Timing Points

*   **Generation Timing**: Initiated via `PerformanceMonitor.start()` and `PerformanceMonitor.stop()` wrapping the `QuizService` generation flow.
*   **Cache Timing**: Not explicitly timed, but status is recorded via `cache_hit` and `fallback_used` flags in `QuizMetrics`.
*   **LLM Timing**: Measured in `QuizService.generate_from_fact` using `time.perf_counter()` and aggregated in `QuizMetrics.llm_time`.
*   **Validation Timing**: Not currently measured. Validation failures are counted (`validation_failures`), but the duration spent in the validation pipeline is not tracked.

## 4. Missing Metrics

*   **Granular Validation Stage Timing**: We track *that* a stage failed, but not *how long* each validation stage (structure, grounding, semantic, etc.) takes.
*   **Per-Note I/O Latency**: We measure note retrieval as a whole, but not the specific latency of reading/processing individual markdown files.
*   **Startup Latency**: The time taken by `MetadataLoader` and `FactCache` during initialization is not explicitly timed as part of the formal metrics.
*   **End-to-End Latency**: While we track generation time, tracking total request latency (from API route entry to response) would provide a better view of user-perceived performance.

## 5. Recommended Monitoring Improvements

1.  **Granular Pipeline Timers**: Instrument each validation stage within `QuizGenerator` to identify which specific validation check is the most expensive.
2.  **Structured/Distributed Logging**: Transition from scattered print statements and fragmented logs to structured JSON logging (e.g., standard Python `logging` with a JSON formatter) to enable easier analysis.
3.  **Tracing**: Implement basic request tracing (e.g., using `contextvars` or OpenTelemetry) to track a request's journey through RAG, generation, and validation phases.
4.  **I/O Instrumentation**: Add explicit timing around disk I/O operations in `MetadataLoader` and `FactCache`.
5.  **Historical Metric Storage**: Currently, metrics are reported per-request in logs. Consider storing historical metrics in a time-series database (e.g., Prometheus/InfluxDB) to track performance trends over time.
