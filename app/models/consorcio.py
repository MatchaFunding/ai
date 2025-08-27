from pydantic import BaseModel, Field
from pydantic.config import ConfigDict

class Consorcio(BaseModel):
    ID: int = Field(...)
    PrimerBeneficiario: int = Field(...)
    SegundoBeneficiario: int = Field(...)

    model_config = ConfigDict(populate_by_name=True)
