from pydantic import BaseModel, Field
from pydantic.config import ConfigDict

class Financiador(BaseModel):
    ID: int = Field(...)
    Nombre: str = Field(...)
    FechaDeCreacion: str = Field(...)
    RegionDeCreacion: str = Field(...)
    Direccion: str = Field(...)
    TipoDePersona: str = Field(...)
    TipoDeEmpresa: str = Field(...)
    Perfil: str = Field(...)
    RUTdeEmpresa: str = Field(...)
    RUTdeRepresentante: str = Field(...)

    model_config = ConfigDict(populate_by_name=True)
