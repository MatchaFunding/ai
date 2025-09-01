from fastapi import APIRouter, Request
from typing import List
from qdrant_client.models import PointStruct
from app.models.instrumento import Instrumento
from app.services.qdrant_store import upsert_points

router = APIRouter(prefix="/funds", tags=["funds"])

def _text_of_fund(inst: Instrumento) -> str:
    return ". ".join(filter(None, [
        inst.Titulo, inst.Descripcion, inst.Requisitos, inst.Beneficios, inst.TipoDePerfil
    ]))

@router.post("/upsert", summary="Indexar/actualizar fondos (batch)")
async def upsert_funds(items: List[Instrumento], request: Request) -> dict:
    provider = request.app.state.provider
    texts = [_text_of_fund(x) for x in items]
    vectors = await provider.embed(texts)

    points = []
    for inst, vec in zip(items, vectors):
        payload = inst.model_dump()
        payload.setdefault("Estado", inst.Estado)
        points.append(PointStruct(id=int(inst.ID), vector=vec, payload=payload))

    upsert_points("funds", points)
    return {"upserted": len(points)}
