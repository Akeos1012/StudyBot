from app.rag.fact_cache import FactCache
from app.rag.retriever import Retriever


def test_retriever_software_topic():
    cache = FactCache()
    cache.load()

    retriever = Retriever(cache)

    facts = retriever.retrieve(
        topic="Software",
        limit=5
    )

    assert isinstance(facts, list)

    for f in facts:
        print(f["concept"])