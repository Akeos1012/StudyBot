from app.models.tutor_schema import NormalizedQuery, TutorIntent
import re

class IntentClassifier:
    def __init__(self):
        self.rules = [
            (TutorIntent.COMPARE, re.compile(r"\b(compare|difference|differences|vs|versus)\b", re.I)),
            (TutorIntent.EXAMPLE, re.compile(r"\b(example|examples|show me|give me)\b", re.I)),
            (TutorIntent.SIMPLIFY, re.compile(r"\b(simplify|simple|easier|easy explanation|explain like)\b", re.I)),
            (TutorIntent.EXPLAIN, re.compile(r"\b(explain|what is|tell me about|define)\b", re.I)),
            (TutorIntent.QUESTION, re.compile(r"\b(how|why)\b", re.I)),
        ]

    def classify(self, query: NormalizedQuery) -> TutorIntent:
        text = query.original_question
        
        for intent, pattern in self.rules:
            if pattern.search(text):
                return intent
        
        return TutorIntent.UNKNOWN
