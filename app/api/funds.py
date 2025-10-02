from fastapi import APIRouter, Request
from typing import List
from qdrant_client.models import PointStruct
from app.models.instrumento import Instrumento
from app.services.qdrant_store import upsert_points
from app.services.embeddings_factory import get_embeddings_provider

router = APIRouter(prefix="/funds", tags=["funds"])

# Junta todos los campos de texto del instrumento en un unico String
def _text_of_fund(i: Instrumento) -> str:
    return ". ".join(filter(None, [
        i.Titulo, i.Descripcion, i.Requisitos, i.Beneficios, i.TipoDePerfil
    ]))

@router.post("/upsert", summary="Indexar/actualizar fondos (batch)")
async def upsert_funds(items: List[Instrumento], request: Request) -> dict:
    provider = request.app.state.provider
    texts = [_text_of_fund(x) for x in items]
    vectors = await provider.embed(texts)
    lista_topic = []
    points = []
    for inst, vec in zip(items, vectors):
        payload = inst.model_dump()
        payload.setdefault("Estado", inst.Estado)
        topics, probs = request.app.state.topic_model.transform(inst.Descripcion)
        topicos = probs[0][1:]

        punto = PointStruct(id=int(inst.ID), vector=topicos, payload=payload)
        lista_topic.append(punto)

        points.append(PointStruct(id=int(inst.ID), vector=vec, payload=payload))

    upsert_points("funds_topics", lista_topic)
    upsert_points("funds", points)

    return {"upserted": len(points)}








