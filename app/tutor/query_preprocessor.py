import re
from typing import List, Optional
from app.models.tutor_schema import NormalizedQuery

class QueryPreprocessor:
    def __init__(self, known_concepts: Optional[List[str]] = None):
        self.known_concepts = known_concepts or []
        self.noise_words = {
            "what", "is", "how", "does", "can", "you", "please", 
            "explain", "tell", "me", "about", "a", "the", "an",
            "between", "of", "in", "to", "for"
        }
        self.spelling_map = {
            "whats": "what is",
            "diff": "difference",
            "db": "database"
        }

    def preprocess(self, question: str) -> NormalizedQuery:
        if not question or not question.strip():
            return NormalizedQuery(
                original_question="",
                normalized_text="",
                keywords=[],
                extracted_concepts=[]
            )

        original = question.strip()
        normalized = original.lower()

        # Spelling
        for bad, good in self.spelling_map.items():
            normalized = re.sub(rf"\b{bad}\b", good, normalized)
        
        # Keyword extraction & noise removal
        words = re.findall(r"\b\w+\b", normalized)
        keywords = [w for w in words if w not in self.noise_words and len(w) > 2]
        
        # Concept extraction (basic matching)
        extracted_concepts = [
            concept for concept in self.known_concepts
            if concept.lower() in normalized
        ]

        return NormalizedQuery(
            original_question=original,
            normalized_text=" ".join(keywords),
            keywords=keywords,
            extracted_concepts=extracted_concepts
        )
