from pydantic import BaseModel, Field
from typing import List

class IdeaProcessed(BaseModel):
    ID: int = Field(...)
    Usuario: int = Field(...)
    Campo: str
    Problema: str
    Publico: str
    Innovacion: str
    Embedding: List[float]
