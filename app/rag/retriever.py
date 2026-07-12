# app/rag/retriever.py
"""
Retriever Module - Retrieves relevant facts from the knowledge base.

Current capabilities:
- Topic-based retrieval
- Difficulty filtering
- Weight-based ranking
- Keyword relevance scoring

Future capabilities:
- Semantic similarity matching
- Concept hierarchy awareness
- Hybrid search (keyword + semantic)

Requires sentence-transformers for embedding search.
"""

from typing import List, Dict, Any, Optional
import logging


# Optional semantic search dependency
try:
    from sentence_transformers import SentenceTransformer
    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False


logger = logging.getLogger(__name__)


class Retriever:
    """
    Retrieves relevant facts from FactCache.

    Current usage:

        retriever = Retriever(fact_cache)

        facts = retriever.retrieve(
            topic="Cloud",
            difficulty="medium",
            limit=10
        )

    Future usage:

        facts = retriever.query(
            "cloud storage services"
        )
    """

    def __init__(
        self,
        fact_cache=None,
        use_embeddings: bool = False
    ):

        self.fact_cache = fact_cache

        self.use_embeddings = (
            use_embeddings and HAS_EMBEDDINGS
        )

        self._embedding_model = None

        if self.use_embeddings:
            self._init_embeddings()


    # =========================================================
    # PHASE 1 RETRIEVAL
    # =========================================================

    def retrieve(
        self,
        topic: str,
        difficulty: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve facts for quiz generation.

        Pipeline:

        Topic
          ↓
        Fact Cache
          ↓
        Difficulty Filter
          ↓
        Weight Ranking
          ↓
        Limit Results
        """

        if not self.fact_cache:
            return []


        facts = self.fact_cache.get_facts(topic)


        if not facts:
            return []


        # Difficulty filtering
        if difficulty:

            filtered = [
                fact
                for fact in facts
                if fact.get("difficulty_hint")
                == difficulty
            ]

            # Keep original facts if no matching difficulty
            if filtered:
                facts = filtered


        # Highest importance first
        facts.sort(
            key=lambda f: (
                f.get("weight", 0),
                len(f.get("definition", ""))
            ),
            reverse=True
        )


        return facts[:limit]



    # =========================================================
    # FUTURE SEMANTIC SEARCH
    # =========================================================

    def query(
        self,
        query_text: str,
        topic: Optional[str] = None,
        max_facts: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Semantic/hybrid query retrieval.

        Used later when the system needs
        meaning-based retrieval.
        """

        if topic:
            candidates = self._get_facts_for_topic(topic)
        else:
            candidates = self._get_all_facts()


        if not candidates:
            return []


        scored = self._score_candidates(
            candidates,
            query_text
        )

        return scored[:max_facts]



    # =========================================================
    # SCORING
    # =========================================================

    def _score_candidates(
        self,
        candidates: List[Dict[str, Any]],
        query: str
    ) -> List[Dict[str, Any]]:

        query_words = set(
            query.lower().split()
        )

        scored = []


        for fact in candidates:

            score = self._keyword_score(
                fact,
                query_words
            )


            if self.use_embeddings:
                semantic_score = self._semantic_score(
                    fact,
                    query
                )

                score = (
                    score * 0.6
                    +
                    semantic_score * 0.4
                )


            scored.append(
                (score, fact)
            )


        scored.sort(
            key=lambda x: x[0],
            reverse=True
        )


        return [
            fact
            for _, fact in scored
        ]



    def _keyword_score(
        self,
        fact: Dict[str, Any],
        query_words: set
    ) -> float:

        text = " ".join(
            [
                fact.get("concept", ""),
                fact.get("definition", ""),
                fact.get("supporting_fact", "")
            ]
        ).lower()


        text_words = set(
            text.split()
        )


        overlap = len(
            text_words & query_words
        )


        if not query_words:
            return 0.5


        return overlap / len(query_words)



    # =========================================================
    # CACHE HELPERS
    # =========================================================

    def _get_facts_for_topic(
        self,
        topic: str
    ) -> List[Dict[str, Any]]:

        if not self.fact_cache:
            return []

        return self.fact_cache.get_facts(topic)



    def _get_all_facts(self) -> List[Dict[str, Any]]:

        if not self.fact_cache:
            return []


        all_facts = []

        for topic in self.fact_cache.get_topics():

            all_facts.extend(
                self.fact_cache.get_facts(topic)
            )


        return all_facts



    # =========================================================
    # EMBEDDING PLACEHOLDERS
    # =========================================================

    def _init_embeddings(self):

        if HAS_EMBEDDINGS:
            self._embedding_model = SentenceTransformer(
                "all-MiniLM-L6-v2"
            )



    def _semantic_score(
        self,
        fact: Dict[str, Any],
        query: str
    ) -> float:

        # Placeholder for future vector similarity
        return 0.0