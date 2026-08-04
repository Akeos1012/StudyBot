from app.tutor.query_preprocessor import QueryPreprocessor
from app.tutor.intent_classifier import IntentClassifier
from app.tutor.query_retriever import QueryRetriever
from app.tutor.fallback_handler import FallbackHandler
from app.tutor.answer_builder import AnswerBuilder
from app.tutor.source_linker import SourceLinker
from app.models.tutor_response import TutorResponse
import logging

logger = logging.getLogger(__name__)

class TutorService:
    def __init__(
        self,
        query_preprocessor: QueryPreprocessor,
        intent_classifier: IntentClassifier,
        query_retriever: QueryRetriever,
        fallback_handler: FallbackHandler,
        answer_builder: AnswerBuilder,
        source_linker: SourceLinker
    ):
        self.query_preprocessor = query_preprocessor
        self.intent_classifier = intent_classifier
        self.query_retriever = query_retriever
        self.fallback_handler = fallback_handler
        self.answer_builder = answer_builder
        self.source_linker = source_linker

    def ask(self, question: str) -> TutorResponse:
        """
        Orchestrates the Personal AI Tutor pipeline.
        """
        if not question or not question.strip():
            return TutorResponse(
                found=False,
                answer="Please provide a valid question.",
                sources=[],
                related_concepts=[],
                intent="UNKNOWN"
            )

        try:
            # 1. Preprocess
            normalized_query = self.query_preprocessor.preprocess(question)
            
            # 2. Classify Intent
            intent = self.intent_classifier.classify(normalized_query)
            
            # 3. Retrieve
            context = self.query_retriever.retrieve(normalized_query)
            
            # 4. Handle Failure/Success
            if not context.found:
                return self.fallback_handler.create_response(context)
            
            # 5. Build Answer
            generated_answer = self.answer_builder.build(context, intent)
            
            # 6. Link Sources
            return self.source_linker.link(context, generated_answer, intent.value)
            
        except Exception as e:
            logger.error(f"TutorService error: {e}", exc_info=True)
            return TutorResponse(
                found=False,
                answer="An error occurred while processing your request.",
                sources=[],
                related_concepts=[],
                intent="UNKNOWN"
            )
