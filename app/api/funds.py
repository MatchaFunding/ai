from fastapi import APIRouter, Request
from typing import List
from qdrant_client.models import PointStruct
from app.models.instrumento import Instrumento
from app.services.qdrant_store import upsert_points
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from app.services.embeddings_factory import get_embeddings_provider


model = SentenceTransformer("jinaai/jina-embeddings-v2-base-es", trust_remote_code=True)
topic_model = BERTopic.load("ayuda", embedding_model = model)


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
    lista_topic = []
    points = []
    for inst, vec in zip(items, vectors):
        payload = inst.model_dump()
        payload.setdefault("Estado", inst.Estado)
        topics, probs = topic_model.transform(inst.Descripcion)
        topicos = probs[0][1:]

        punto = PointStruct(id=int(inst.ID), vector=topicos, payload=payload)
        lista_topic.append(punto)

        points.append(PointStruct(id=int(inst.ID), vector=vec, payload=payload))

    upsert_points("funds_topics", lista_topic)
    upsert_points("funds", points)

    return {"upserted": len(points)}








