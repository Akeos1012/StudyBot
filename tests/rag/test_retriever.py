from app.rag.fact_cache import FactCache
from app.rag.retriever import Retriever

cache = FactCache()
cache.load()

retriever = Retriever(cache)

facts = retriever.retrieve(topic="Software", limit=5)

print()

for f in facts:
    print(f["concept"])
