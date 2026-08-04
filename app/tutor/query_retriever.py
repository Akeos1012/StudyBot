from app.models.tutor_schema import NormalizedQuery
from app.models.retrieved_context import RetrievedContext
from app.rag.retriever import Retriever
import logging

logger = logging.getLogger(__name__)

class QueryRetriever:
    def __init__(self, retriever: Retriever):
        self.retriever = retriever

    def retrieve(self, query: NormalizedQuery) -> RetrievedContext:
        """
        Coordinates retrieval, validates context, and limits results.
        """
        # Call Retriever.search()
        context = self.retriever.search(query)
        
        if not context.found:
            return context
        
        # Limit to 5 facts and sync other fields
        limit = 5
        
        # Slice lists to the limit
        context.facts = context.facts[:limit]
        
        # Refresh metadata lists based on sliced facts
        context.concepts = sorted(list(set(f.get("concept") for f in context.facts if f.get("concept"))))
        context.topics = sorted(list(set(f.get("topic") for f in context.facts if f.get("topic"))))
        context.sources = sorted(list(set(f.get("source") for f in context.facts if f.get("source"))))
        context.supporting_facts = [f.get("definition") for f in context.facts if f.get("definition")]

        # Validate metadata integrity
        for fact in context.facts:
            required = ["fact_id", "source", "definition", "concept", "topic"]
            if not all(k in fact for k in required):
                logger.warning(f"Fact missing required metadata: {fact.get('fact_id', 'unknown')}")
        
        return context
