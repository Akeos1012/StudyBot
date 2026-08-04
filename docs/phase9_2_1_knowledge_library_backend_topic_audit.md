# Knowledge Library Backend Topic API Audit - Phase 9.2.1

## 1. Current Knowledge Pipeline
Notes (Obsidian Vault) -> `MetadataLoader` (extracts metadata) -> `FactExtractor` -> `FactCache` -> Quiz Pipeline.

## 2. Topic Storage Source
- **Truth**: The `topic` is derived from the Obsidian folder structure or frontmatter in `MetadataLoader`. 
- **Storage**: `MetadataLoader` manages the metadata index in `.metadata.json`. Topics are also keys in `FactCache` (`app/rag/fact_cache.py`).

## 3. Obsidian Mapping Rules
- `MetadataLoader` recursively finds markdown files.
- `topic`: Taken from frontmatter `topic` field or parent folder name.
- `subtopic`: Taken from frontmatter `subtopic` field or filename (`md_file.stem`).

## 4. Existing API Inventory
- `POST /refresh-notes` (app/api/routes.py): Rebuilds metadata cache and returns list of topics.
- `GET /analytics/weak-topics` (app/api/analytics_routes.py): Returns weak topics for analytics, not available topics in knowledge library.
- **Missing**: A dedicated `GET /knowledge/topics` API to list all topics with note/fact counts.

## 5. Frontend Data Requirements
- Topic list: `topic` name, `note_count`, `fact_count`, `last_updated`.

## 6. Missing Backend Pieces
- A new API endpoint is required to provide the requested frontend topic list with aggregated counts.
- `QuizSessionService` or `MetadataLoader` needs to provide a method to get aggregated note/fact counts per topic.

## 7. Recommended API Contract
### `GET /knowledge/topics`
**Response:**
```json
{
  "topics": [
    {
      "name": "Python",
      "note_count": 10,
      "fact_count": 50,
      "last_updated": "2026-08-03T01:00:00Z"
    }
  ]
}
```

## 8. Implementation Recommendation
**BLOCKED - BACKEND TOPIC DATA SOURCE/API MISSING**
Need to implement `GET /knowledge/topics` and aggregate note/fact counts before UI work.
