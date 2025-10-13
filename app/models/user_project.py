from pydantic import BaseModel, Field
from pydantic.config import ConfigDict

class UserProject(BaseModel):
    ID: int = Field(...)
    Idea: int = Field(...)
    User: int = Field(...)
    Beneficiario: int = Field(...)
    Titulo: str = Field(...)
    Descripcion: str = Field(...)
    DuracionEnMesesMinimo: int = Field(...)
    DuracionEnMesesMaximo: int = Field(...)
    Alcance: str = Field(...)
    Area: str = Field(...)

    model_config = ConfigDict(populate_by_name=True)