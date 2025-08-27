# app/models/__init__.py
from .idea import Idea
from .usuario import Usuario
from .beneficiario import Beneficiario
from .colaborador import Colaborador
from .consorcio import Consorcio
from .financiador import Financiador
from .instrumento import  Instrumento

__all__ = [
    "Idea",
    "Usuario",
    "Beneficiario",
    "Colaborador",
    "Consorcio",
    "Financiador",
    "Instrumento",
]
