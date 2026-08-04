from pydantic import BaseModel
from typing import List, Dict, Any

class RetrievedContext(BaseModel):
    found: bool
    facts: List[Dict[str, Any]]
    concepts: List[str]
    topics: List[str]
    sources: List[str]
    supporting_facts: List[str]
