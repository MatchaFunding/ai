from fastapi import APIRouter
from app.models.idea import Idea

router = APIRouter(prefix="/ideas", tags=["ideas"])

@router.post("/", response_model=Idea, summary="Crear/validar una Idea (echo)")
def create_idea(idea: Idea) -> Idea:
    """
    Endpoint mínimo para validar contrato de entrada/salida con el modelo Idea.
    Por ahora retorna un eco del payload (sirve para tests y para alinear frontend/backend).
    """
    return idea
