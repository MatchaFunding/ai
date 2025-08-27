from pydantic import BaseModel, Field
from pydantic.config import ConfigDict

class Usuario(BaseModel):
    ID: int = Field(...)
    Persona: int = Field(...)
    NombreDeUsuario: str = Field(...)
    Contrasena: str = Field(...)
    Correo: str = Field(...)

    model_config = ConfigDict(populate_by_name=True)
