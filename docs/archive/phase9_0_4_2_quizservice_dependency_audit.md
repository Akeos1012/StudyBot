# QuizService Dependency Audit - Phase 9.0.4.2

## QuizService Instantiation Map

`app/main.py`
 |
 `QuizService(...)`
 |
 dependencies (MetadataLoader, QuizGenerator, PoolManager, MasteryService, HistoryService, LearningAnalyticsService, RecommendationEngine, AnalyticsRepository)

## Required Constructor Parameters

| Parameter Name | Source File | Why QuizService needs it |
| :--- | :--- | :--- |
| `metadata_loader` | `app/rag/metadata_loader.py` | To retrieve notes for a topic. |
| `quiz_generator` | `app/quiz/quiz_generator.py` | To generate questions and manage cache. |
| `pool_manager` | `app/quiz/pool_manager.py` | To manage pool health and expansion. |
| `mastery_service` | `app/learning/mastery_service.py` | To update/check user mastery. |
| `history_service` | `app/learning/history_service.py` | (Implicit, needed for constructor compatibility) |
| `analytics_service` | `app/learning/analytics_service.py` | To record analytics and get learning summaries. |
| `recommendation_engine` | `app/learning/recommendation_engine.py` | To get concept weights. |
| `analytics_repository` | `app/learning/analytics/analytics_repository.py` | To record learning events. |

## Existing Public Interface

- `create_quiz_session()`
- `generate_questions_for_topic()`
- `get_or_generate_questions()`
- `submit_session_answer()`
- `record_answer()`
- `generate_fill_blank_questions()`
