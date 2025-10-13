from pydantic import BaseModel, Field
from pydantic.config import ConfigDict
from typing import List, Optional

class MatchRequest(BaseModel):
    idea_id: int = Field(..., description="ID de la idea ya procesada y guardada en Qdrant")
    top_k: int = 10
    estado: Optional[str] = "abierto"
    regiones: Optional[List[str]] = None
    tipos_perfil: Optional[List[str]] = None

    model_config = ConfigDict(populate_by_name=True)