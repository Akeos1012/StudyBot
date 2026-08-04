from pydantic import BaseModel
from typing import List
from enum import Enum

class TutorIntent(Enum):
    EXPLAIN = "EXPLAIN"
    SIMPLIFY = "SIMPLIFY"
    COMPARE = "COMPARE"
    EXAMPLE = "EXAMPLE"
    QUESTION = "QUESTION"
    UNKNOWN = "UNKNOWN"

class NormalizedQuery(BaseModel):
    original_question: str
    normalized_text: str
    keywords: List[str]
    extracted_concepts: List[str]
    intent: str = TutorIntent.UNKNOWN.value
    question_style: str = TutorIntent.UNKNOWN.value
