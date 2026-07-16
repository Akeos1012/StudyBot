# StudyBot Changelog

All notable changes to this project are documented here.

The format follows a simple version history:

* Added: New features
* Changed: Existing behavior modified
* Fixed: Bugs resolved
* Removed: Deprecated features removed
* Performance: Speed or resource improvements

---

# v0.6.0 - Performance Optimization (Current)

## Added

* Added performance monitoring foundation.
* Added `performance_profiler.py` utility.
* Added quiz generation timing measurement.
* Added monitoring module for quiz metrics.
* Added structured validation logging.

## Changed

* Improved project organization:

  * Separated API layer.
  * Separated service layer.
  * Separated RAG pipeline.
  * Separated quiz generation modules.
* Improved fact cache loading process.
* Improved question validation pipeline.
* Improved question grounding against extracted facts.

## Fixed

* Fixed invalid question generation cases.
* Fixed duplicate question handling.
* Fixed explanation validation issues.
* Fixed fact normalization problems.

## Architecture Status

Current pipeline:

```
Obsidian Vault

↓

Metadata Loader

↓

Fact Extractor

↓

Fact Cache

↓

Question Builder

↓

Validation Pipeline

↓

AI Enhancement

↓

Quiz Output
```

## Current Metrics

* Extracted Facts: 280
* Topics Loaded: 15+
* Knowledge Source: Obsidian Vault
* LLM Role: Enhancement only
* Ground Truth: Local fact cache

---

# v0.5.0 - API Layer

## Added

* FastAPI application layer.
* Quiz generation endpoint.
* Topic retrieval endpoint.
* Cache status endpoint.
* Note refresh endpoint.

## Changed

* Connected quiz pipeline to API services.
* Added request/response handling.

---

# v0.4.0 - Validation Pipeline

## Added

* Schema validation.
* Semantic validation.
* Domain validation.
* Duplicate detection.
* Explanation validation.
* Quality scoring.

## Changed

* Questions are now rejected when they are not grounded in extracted knowledge.

---

# v0.3.0 - Quiz Generation Engine

## Added

* Rule-based question builder.
* Distractor generation.
* Explanation generation.
* Question cache.
* Retry handling.

## Changed

* AI generation changed from knowledge creation into question enhancement.

---

# v0.2.0 - Knowledge Pipeline

## Added

* Markdown parsing.
* Fact extraction.
* Fact cleaning.
* Fact normalization.
* Topic organization.
* Fact cache system.

## Changed

* Obsidian became the source of truth.

---

# v0.1.0 - Foundation

## Added

* Initial project architecture.
* FastAPI structure.
* Modular components.
* Service layer.
* LLM client abstraction.
* Initial folder organization.

---

# Future Releases

## v0.7.0

Planned:

* Centralized configuration.
* Logging improvements.
* Version management.
* Documentation cleanup.

## v0.8.0

Planned:

* Fill-in-the-blank engine.
* Advanced question types.

## v0.9.0

Planned:

* Automated testing.
* CI pipeline.
* Quality improvements.

## v1.0.0

Production release:

* Stable architecture.
* Optimized performance.
* Frontend application.
* Desktop application.
* AI tutor features.
