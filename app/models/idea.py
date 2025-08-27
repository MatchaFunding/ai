from pydantic import BaseModel, Field
from pydantic.config import ConfigDict

class Idea(BaseModel):
    ID: int = Field(...)
    Usuario: int = Field(...)
    Campo: str = Field(...)
    Problema: str = Field(...)
    Publico: str = Field(...)
    Innovacion: str = Field(...)

    model_config = ConfigDict(populate_by_name=True)
