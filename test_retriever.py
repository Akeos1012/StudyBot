from app.rag.fact_cache import FactCache
from app.rag.retriever import Retriever


def main():

    print("=" * 50)
    print("Testing Retriever")
    print("=" * 50)

    # Load facts
    cache = FactCache()
    cache.load()

    # Create retriever
    retriever = Retriever(cache)


    # Test topic retrieval
    facts = retriever.retrieve(
        topic="Cloud",
        difficulty="medium",
        limit=5
    )


    print("\nRetrieved facts:")
    print(f"Count: {len(facts)}\n")


    for fact in facts:
        print(
            f"- {fact['concept']}"
        )
        print(
            f"  Difficulty: {fact.get('difficulty_hint')}"
        )
        print(
            f"  Weight: {fact.get('weight')}"
        )
        print()



if __name__ == "__main__":
    main()