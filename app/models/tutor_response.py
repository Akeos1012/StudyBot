from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class TutorResponse(BaseModel):
    found: bool
    answer: str
    sources: List[str]
    related_concepts: List[str]
    intent: str
    metadata: Dict[str, Any] = {}
