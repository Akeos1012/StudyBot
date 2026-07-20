# StudyBot Changelog

All notable changes to this project are documented here.

Version history uses the following categories:

* **Added** – New functionality
* **Changed** – Existing behavior modified
* **Fixed** – Bugs resolved
* **Removed** – Deprecated or obsolete features
* **Performance** – Speed and resource improvements
* **Architecture** – Structural improvements

---

# v0.6.0 - Performance Optimization & Grounding Refactor (Current)

## Added

### Performance

* Added performance monitoring foundation.
* Added `performance_profiler.py`.
* Added generation time measurements.
* Added quiz metrics collection.
* Added structured validation logging.

### Grounding

* Added `correct_text` field to generated questions.
* Added `supporting_fact` attachment for every accepted question.
* Added automatic `fact_id` generation.
* Added `source_note` tracking.
* Added supporting fact normalization.
* Added supporting fact selection logic.
* Added grounded explanation generation from extracted facts.
* Added context fallback when supporting facts are unavailable.

### Validation

* Added improved grounding validation using:

  * exact matching
  * keyword overlap
  * descriptive matching
  * phrase-level matching
* Added semantic explanation validation against supporting facts.
* Added ambiguity detection improvements.
* Added detailed validation logging.

---

## Changed

### Architecture

Project structure is now clearly separated into independent layers:

* API
* Services
* RAG pipeline
* Quiz generation
* Monitoring
* Validation

### Quiz Pipeline

The quiz generation pipeline has been heavily refactored.

Questions now flow through:

```
Fact Cache
      │
      ▼
Question Builder
      │
      ▼
Grounding Layer
      │
      ▼
Semantic Validation
      │
      ▼
Quality Scoring
      │
      ▼
Final Quiz
```

### Explanation Pipeline

Explanation handling has been redesigned.

Previously:

```
LLM
   │
   ▼
Generated explanation
```

Current design:

```
LLM
   │
   ▼
Question Builder
   │
   ▼
Grounding Layer
   │
   ▼
Attach supporting fact
   │
   ▼
Generate fact-based explanation
   │
   ▼
Semantic validation
```

This ensures every accepted explanation is grounded in the extracted knowledge base.

### Grounding

Grounding now relies on extracted supporting facts instead of only raw note context.

Supporting facts are normalized before validation.

Fact metadata now remains attached throughout the generation pipeline.

---

## Fixed

### Grounding

* Fixed incorrect grounding failures.
* Fixed missing supporting facts.
* Fixed inconsistent fact normalization.
* Fixed incorrect context fallback behavior.

### Explanations

* Fixed explanation generation inconsistencies.
* Fixed explanations that ignored extracted facts.
* Fixed explanation attachment logic.
* Prevented explanations from being regenerated unnecessarily once a valid explanation exists.
* Reduced duplicate explanation generation across the pipeline.

### Validation

* Fixed duplicate question detection.
* Fixed semantic validation edge cases.
* Fixed ambiguity validation issues.
* Fixed invalid question rejection logic.

### General

* Fixed fact cache normalization.
* Fixed invalid facts remaining inside cache.
* Fixed multiple validation edge cases discovered during refactoring.

---

## Performance

Current optimizations include:

* Faster fact normalization.
* Reduced unnecessary explanation generation.
* Reduced repeated grounding work.
* Improved validation efficiency.
* Better separation between generation and validation stages.

---

## Architecture Status

Current pipeline:

```
Obsidian Vault
        │
        ▼
Metadata Loader
        │
        ▼
Fact Extractor
        │
        ▼
Fact Cache
        │
        ▼
Question Builder
        │
        ▼
Grounding Layer
        │
        ▼
Validation Pipeline
        │
        ▼
Quality Scoring
        │
        ▼
AI Enhancement (wording only)
        │
        ▼
Quiz Output
```

---

## Current Project Status

Knowledge Source

* Obsidian Vault

Ground Truth

* Local fact cache

Question Generation

* Rule-based

LLM Responsibility

* Question wording
* Explanation enhancement
* Language improvement

LLM does **not** create knowledge.

Facts always originate from the extracted note cache.

---

# v0.5.0 - API Layer

## Added

* FastAPI application.
* Quiz generation endpoint.
* Topic endpoint.
* Cache status endpoint.
* Note refresh endpoint.

## Changed

* Connected API to service layer.
* Standardized request and response models.

---

# v0.4.0 - Validation Pipeline

## Added

* Schema validation.
* Semantic validation.
* Grounding validation.
* Domain validation.
* Duplicate detection.
* Ambiguity detection.
* Quality scoring.
* Explanation validation.

## Changed

Questions are rejected unless they:

* follow schema,
* are semantically correct,
* are grounded in extracted facts,
* pass quality scoring.

---

# v0.3.0 - Quiz Generation Engine

## Added

* Rule-based question builder.
* Distractor generation.
* Question cache.
* Retry mechanism.
* AI-assisted wording improvement.
* Fact-based explanation generation.

## Changed

AI transitioned from knowledge generation to enhancement only.

---

# v0.2.0 - Knowledge Pipeline

## Added

* Markdown parser.
* Metadata extraction.
* Fact extraction.
* Fact cleaning.
* Fact normalization.
* Topic organization.
* Fact cache.

## Changed

Obsidian became the single source of truth.

---

# v0.1.0 - Foundation

## Added

* Initial project architecture.
* Modular folder structure.
* Service layer.
* FastAPI integration.
* LLM abstraction.
* Initial RAG pipeline.

---

# Future Releases

## v0.7.0

Planned

* Centralized configuration.
* Performance dashboard.
* Configuration management.
* Logging improvements.
* Architecture cleanup.
* Monitoring integration.
* Version management.

---

## v0.8.0

Planned

* Fill-in-the-blank questions.
* True/False questions.
* Matching questions.
* Difficulty balancing.
* Adaptive quiz generation.

---

## v0.9.0

Planned

* Automated testing.
* Integration testing.
* Benchmark suite.
* CI/CD pipeline.
* Coverage reporting.

---

# v1.0.0 - Production

Goals

* Stable architecture.
* Optimized performance.
* Desktop application.
* AI Study Companion.
* Interactive tutor mode.
* Progress tracking.
* Learning analytics.
* Production-ready documentation.
