from typing import Optional, List, Any
from pydantic import BaseModel, Field



class QuizRequest(BaseModel):
    topic: str = "Database"
    subtopic: Optional[str] = ""
    difficulty: str = "medium"
    count: int = Field(default=3, ge=1, le=50)
    fresh: bool = False


class FillBlankRequest(BaseModel):
    topic: str = "Database"
    subtopic: Optional[str] = ""
    difficulty: str = "medium"
    count: int = Field(default=3, ge=1, le=50)
    fresh: bool = False

class QuestionResponse(BaseModel):
    topic: Optional[str] = None
    subtopic: Optional[str] = None
    difficulty: Optional[str] = None
    source_note: Optional[str] = None
    concept_type: Optional[str] = None
    question_id: Optional[str] = None
    question: str
    type: str
    explanation: str = ""
    correct: Optional[str] = None
    correct_text: Optional[str] = None
    options: List[str] = Field(default_factory=list)
    supporting_fact: Optional[str] = None
    concept: Optional[str] = None
    fact_id: Optional[str] = None

class QuizResponse(BaseModel):
    success: bool = True
    topic: str
    subtopic: Optional[str] = None
    difficulty: Optional[str] = None
    question_type: Optional[str] = None
    count: int = 0
    questions: List[QuestionResponse]
    source_notes: List[str]


class TopicResponse(BaseModel):
    topics: List[str]


class NotesResponse(BaseModel):
    topic: str
    notes: List[dict]