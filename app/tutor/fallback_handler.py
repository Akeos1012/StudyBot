from app.models.retrieved_context import RetrievedContext
from app.models.tutor_response import TutorResponse

class FallbackHandler:
    def create_response(self, context: RetrievedContext) -> TutorResponse:
        """
        Generates a static fallback response when retrieval fails.
        """
        if context.found:
            raise ValueError("FallbackHandler should only be used when context.found is False")

        return TutorResponse(
            found=False,
            answer="I couldn't find this topic in your knowledge base. Consider adding notes about this topic.",
            sources=[],
            related_concepts=[],
            intent="UNKNOWN"
        )
