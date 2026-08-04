"""
Smart Reviewer Result Schema

Purpose:
    Represents the runtime learning feedback generated after a student
    submits an answer to a question.

    This model is separate from QuestionSchema, which represents static
    quiz content.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class SmartReviewerResult(BaseModel):
    """
    Data model for the result of a student's answer review event.
    """
    question_id: str
    user_answer: str
    correct_answer: str
    is_correct: bool
    explanation: str
    supporting_fact: Optional[str] = None
    source_note: Optional[str] = None
    fact_id: str
    related_concepts: List[str] = Field(default_factory=list)
    review_metadata: Dict[str, Any] = Field(default_factory=dict)
