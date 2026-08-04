# Phase 7: Personal AI Tutor Architecture Audit

## 1. Audit Summary
The StudyBot system demonstrates a strong foundation for a Personal AI Tutor. The current RAG pipeline (loader -> extraction -> cache -> retrieval) provides a secure, grounded environment that inherently prevents unauthorized knowledge usage. The system is well-structured, but requires enhancement in its retrieval strategy and a new orchestration layer to manage natural language tutor interactions.

## 2. Current Architecture Compatibility
The architecture is **highly compatible**. The existing `FactCache` serves as the authoritative source of truth. No components bypass this layer, making it safe to build the Tutor on top of the established pipeline.

## 3. Knowledge Flow Diagram
```text
[Student Query]
      ↓
[Query Processor/Intent Classifier]
      ↓
[Retriever] <---> [FactCache]
      ↓
[Answer Builder (LLM)] <--- [Grounded Facts]
      ↓
[Tutor Response (w/ Source Traceability)]
```

## 4. Retrieval Strategy Decision
**Recommendation: Hybrid Retrieval (Keyword + Concept matching)**
For V1, strict keyword and concept-based retrieval is recommended over raw semantic similarity to ensure deterministic behavior and minimize hallucination risk.
- **Valid Retrieval:** Facts matching the concept or topic of the query.
- **Invalid Retrieval:** Random semantic matches without a verifiable source link.
- **Fallback:** If no facts are found in the `FactCache` for the query's topic/concepts, the system must refuse to answer.

## 5. Data Contracts
### Student Query
```json
{
  "question": "string",
  "preferences": { "style": "detailed" | "simple" }
}
```
### Retrieved Context
```json
{
  "facts": ["list of validated fact dicts"],
  "sources": ["list of note paths"],
  "confidence": "float"
}
```
### Tutor Response
```json
{
  "found": "boolean",
  "answer": "string",
  "sources": ["list of source_note paths"],
  "related_concepts": ["list"],
  "intent": "string"
}
```

## 6. Component Dependency Map
| Component | Status | Responsibility | Reused? |
| :--- | :--- | :--- | :--- |
| `FactCache` | Existing | Authoritative knowledge store | Yes |
| `Retriever` | Existing | Fact lookup | Yes (needs enhancement) |
| `TutorService` | New | Orchestrates Tutor logic | No |
| `AnswerBuilder` | New | LLM wrapper for grounded answers | No (use QuizGenerator logic) |
| `API Route` | New | `POST /tutor/ask` | No |

## 7. AI Boundary Rules
*   **Allowed:** Fact retrieval, summarization, simplification, example generation.
*   **Forbidden:** Answering from model memory, inferring facts, modifying source knowledge.
*   **Enforcement:**
    1.  The system prompt must explicitly state: "Answer ONLY using the provided facts. If the answer is not in the facts, state you do not know."
    2.  Empty context MUST trigger an immediate "not found" response before the LLM is invoked.

## 8. Retrieval Quality Rules
*   **Level 1 (Required):** Exact concept/topic match.
*   **Level 2 (Optional):** Validated facts within the same topic.
*   **Rejection:** Any retrieval not mapped to a validated fact in `FactCache` must be rejected to prevent hallucination.

## 9. Risks and Mitigations
*   **Risk:** Weak retrieval returns empty context for valid questions.
    *   *Mitigation:* Enhance `Retriever` to support multi-concept keyword searching.
*   **Risk:** LLM ignores grounding instructions.
    *   *Mitigation:* Strict system prompt, forced-citation requirement, and automated pre-LLM context check.

## 10. Recommended Implementation Order
1.  **Contract Definition:** Create `app/models/tutor_schema.py`.
2.  **Retrieval Improvements:** Update `Retriever` to handle concept-based queries reliably.
3.  **Tutor Service:** Build `app/services/tutor_service.py` to manage logic and grounding.
4.  **API Integration:** Define `POST /tutor/ask` in `routes.py`.
5.  **Testing:** Build comprehensive test suite verifying grounding compliance.

## 11. Phase 7 Implementation Readiness
**READY FOR IMPLEMENTATION**
