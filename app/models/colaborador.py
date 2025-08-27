from pydantic import BaseModel, Field
from pydantic.config import ConfigDict

class Colaborador(BaseModel):
    ID: int = Field(...)
    Persona: int = Field(...)
    Proyecto: int = Field(...)

    model_config = ConfigDict(populate_by_name=True)
