from app.models.retrieved_context import RetrievedContext
from app.models.tutor_schema import TutorIntent
from app.tutor.prompts import SYSTEM_PROMPT, INTENT_TEMPLATES
from app.quiz.generation.llm_client import LLMClient

class AnswerBuilder:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def build(self, context: RetrievedContext, intent: TutorIntent) -> str:
        """
        Transforms retrieved knowledge into a student-friendly explanation.
        """
        if not context.found:
            raise ValueError("Cannot build answer from empty context")

        # Construct context block
        context_lines = []
        for fact in context.facts:
            context_lines.append(f"Fact: {fact.get('definition', '')}")
        context_text = "\n".join(context_lines)

        # Build prompts
        system_prompt = SYSTEM_PROMPT.format(context=context_text)
        user_prompt = INTENT_TEMPLATES.get(intent, INTENT_TEMPLATES[TutorIntent.EXPLAIN])

        # Generate answer
        return self.llm_client.generate_with_system(system_prompt, user_prompt)
