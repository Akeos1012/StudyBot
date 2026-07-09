# app/rag/retriever.py - Advanced Version
"""
Retriever Module - Retrieves relevant facts from the knowledge base.

This module provides advanced retrieval with:
- Semantic similarity matching
- Concept hierarchy awareness
- Hybrid search (keyword + semantic)

Requires sentence-transformers or similar embedding library.
"""

from typing import List, Dict, Any, Optional
import logging

# Optional: For semantic search
try:
    from sentence_transformers import SentenceTransformer
    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False

logger = logging.getLogger(__name__)


class Retriever:
    """
    Advanced retriever with semantic search capabilities.

    Usage:
        retriever = Retriever(fact_cache, use_embeddings=True)
        facts = retriever.query("cloud storage services")
    """

    def __init__(self, fact_cache=None, use_embeddings: bool = False):
        self.fact_cache = fact_cache
        self.use_embeddings = use_embeddings and HAS_EMBEDDINGS
        self._embedding_model = None

        if self.use_embeddings:
            self._init_embeddings()

    def query(self, query_text: str, topic: Optional[str] = None,
             max_facts: int = 10) -> List[Dict[str, Any]]:
        """
        Query the knowledge base.

        Args:
            query_text: The query text
            topic: Optional topic filter
            max_facts: Maximum facts to return

        Returns:
            List of relevant facts
        """
        # Get candidate facts
        if topic:
            candidates = self._get_facts_for_topic(topic)
        else:
            candidates = self._get_all_facts()

        if not candidates:
            return []

        # Score candidates
        scored = self._score_candidates(candidates, query_text)

        return scored[:max_facts]

    def _score_candidates(self, candidates: List[Dict[str, Any]], 
                         query: str) -> List[Dict[str, Any]]:
        """Score candidates by relevance to query."""
        # Keyword scoring
        query_words = set(query.lower().split())
        scored = []

        for fact in candidates:
            score = self._keyword_score(fact, query_words)

            # Add semantic score if available
            if self.use_embeddings:
                semantic_score = self._semantic_score(fact, query)
                score = score * 0.6 + semantic_score * 0.4

            scored.append((score, fact))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [f for _, f in scored]

    def _keyword_score(self, fact: Dict[str, Any], 
                      query_words: set) -> float:
        """Compute keyword-based relevance score."""
        text = " ".join([
            fact.get("concept", ""),
            fact.get("definition", ""),
            fact.get("supporting_fact", "")
        ]).lower()

        text_words = set(text.split())
        overlap = len(text_words & query_words)

        if not query_words:
            return 0.5

        return overlap / len(query_words)