from pydantic import BaseModel, Field
from pydantic.config import ConfigDict

class Instrumento(BaseModel):
    ID: int = Field(...)
    Titulo: str = Field(...)
    Financiador: int = Field(...)
    Alcance: str = Field(...)
    Descripcion: str = Field(...)
    FechaDeApertura: str = Field(...)
    FechaDeCierre: str = Field(...)
    DuracionEnMeses: int = Field(...)
    Beneficios: str = Field(...)
    Requisitos: str = Field(...)
    MontoMinimo: int = Field(...)
    MontoMaximo: int = Field(...)
    Estado: str = Field(...)
    TipoDeBeneficio: str = Field(...)
    TipoDePerfil: str = Field(...)
    EnlaceDelDetalle: str = Field(...)
    EnlaceDeLaFoto: str = Field(...)

    model_config = ConfigDict(populate_by_name=True)
