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

class QuizResponse(BaseModel):
    topic: str
    subtopic: Optional[str] = None
    questions: List[dict]
    source_notes: List[str]


class TopicResponse(BaseModel):
    topics: List[str]


class NotesResponse(BaseModel):
    topic: str
    notes: List[dict]