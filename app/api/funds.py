from fastapi import APIRouter, Request
from typing import List
from qdrant_client.models import PointStruct
from app.models.instrumento import Instrumento
from app.services.qdrant_store import upsert_points

from app.services.embeddings_factory import get_embeddings_provider
from bertopic import BERTopic
topic_model = BERTopic.load("ayuda", embedding_model = get_embeddings_provider())


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
        topics, probs = topic_model.transform(payload.Descripcion)
        topicos = probs[0][1:]
        client.upsert(
        collection_name="QDRANT_FUNDS_TOPICS_COLLECTION",
        points=[
            PointStruct(
                id=payload.ID,
                vector=topicos,
                payload=payload
                )
            ]
        )

        points.append(PointStruct(id=int(inst.ID), vector=vec, payload=payload))


    upsert_points("funds", points)






    return {"upserted": len(points)}








