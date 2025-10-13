from pydantic import BaseModel, Field
from pydantic.config import ConfigDict
from typing import List, Optional

class MatchResult(BaseModel):
    call_id: int
    name: str
    agency: Optional[str] = None
    affinity: float
    semantic_score: float
    rules_score: float
    topic_score: float 
    explanations: List[str] = []

    model_config = ConfigDict(populate_by_name=True)