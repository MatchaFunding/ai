from pydantic import BaseModel, Field

class IdeaRefinada(BaseModel):
    ID: int = Field(...)
    Usuario: int = Field(...)
    ResumenLLM: str = Field(..., description="Párrafo refinado por LLM")
