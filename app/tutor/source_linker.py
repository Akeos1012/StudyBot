from app.models.retrieved_context import RetrievedContext
from app.models.tutor_response import TutorResponse
from typing import List

class SourceLinker:
    def link(self, context: RetrievedContext, answer: str, intent: str) -> TutorResponse:
        """
        Attaches verified source metadata from context to the generated answer.
        """
        if not context.found:
            return TutorResponse(
                found=False,
                answer=answer,
                sources=[],
                related_concepts=[],
                intent=intent
            )

        # Extract unique sources only from retrieved facts
        # Note: fact schema uses 'source' for note path
        sources = sorted(list(set(f.get("source") for f in context.facts if f.get("source"))))
        
        # Use existing context concepts
        related_concepts = context.concepts

        return TutorResponse(
            found=True,
            answer=answer,
            sources=sources,
            related_concepts=related_concepts,
            intent=intent,
            metadata={"source_count": len(sources)}
        )
