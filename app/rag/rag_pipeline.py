"""
RAG Pipeline Controller

Connects:
- Metadata loading
- Fact extraction
- Grounding
- Cleaning
- Cache generation
- Retrieval

This module controls the RAG workflow.
"""

from typing import List, Dict, Any

from .metadata_loader import MetadataLoader
from .fact_extractor import FactExtractor
from .grounding_processor import GroundingProcessor
from .fact_cleaner import clean_facts
from .fact_cache import FactCache
from .retriever import Retriever


class RAGPipeline:

    def __init__(self, notes_path="sample_notes"):
        self.notes_path = notes_path

        self.metadata_loader = MetadataLoader(notes_path)
        self.extractor = FactExtractor(notes_path)
        self.grounder = GroundingProcessor()
        self.cache = FactCache(notes_path)

        self.retriever = Retriever(
            self.cache,
            use_embeddings=False
        )


    def build(self):
        """
        Full knowledge pipeline build.
        """

        print("🚀 Starting RAG Pipeline")

        # Step 1: Load metadata
        print("\n📚 Loading metadata...")
        metadata = self.metadata_loader.load_metadata()

        print(
            f"✅ Loaded {len(metadata)} notes"
        )


        # Step 2: Extract facts
        print("\n🔎 Extracting facts...")

        raw_facts = self.extractor.extract_all()


        total = sum(
            len(v)
            for v in raw_facts.values()
        )

        print(
            f"✅ Extracted {total} facts"
        )


        # Step 3: Ground facts

        print("\n⚙️ Grounding facts...")


        grounded = {}

        for topic, facts in raw_facts.items():

            processed = self.grounder.ground_all(
                facts
            )

            if processed:
                grounded[topic] = processed


        total_grounded = sum(
            len(v)
            for v in grounded.values()
        )

        print(
            f"✅ Grounded {total_grounded} facts"
        )


        # Step 4: Clean facts

        print("\n🧹 Cleaning facts...")


        cleaned = {
            topic: clean_facts(facts)
            for topic, facts in grounded.items()
        }


        # Step 5: Save cache

        print("\n💾 Saving cache...")


        self.cache.cache = cleaned
        self.cache.save_cache()


        print("\n🎉 RAG Pipeline completed")


        return cleaned



    def search(
        self,
        query: str,
        topic=None,
        limit=5
    ) -> List[Dict[str, Any]]:

        """
        Search knowledge base.
        """

        return self.retriever.query(
            query,
            topic,
            limit
        )



if __name__ == "__main__":

    pipeline = RAGPipeline()

    pipeline.build()


    print("\n🔍 Testing retrieval")

    results = pipeline.search(
        "cloud storage"
    )


    for fact in results:
        print(
            f"- {fact['concept']}"
        )