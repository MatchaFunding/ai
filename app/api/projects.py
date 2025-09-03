from fastapi import APIRouter, Request
from typing import List
from qdrant_client.models import PointStruct
from app.models.proyecto import Proyecto
from app.services.qdrant_store import upsert_points
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from app.services.embeddings_factory import get_embeddings_provider




router = APIRouter(prefix="/projects", tags=["projects"])

def _text_of_proyect(inst: Proyecto) -> str:
    return ". ".join(filter(None, [
        inst.Titulo, inst.Descripcion, inst.Alcance, inst.Area
    ]))



@router.post("/upsert", summary="Indexar/actualizar proyectos (batch)")
async def upsert_proyects(items: List[Proyecto], request: Request) -> dict:
    provider = request.app.state.provider
    texts = [_text_of_proyect(x) for x in items]
    vectors = await provider.embed(texts)
    lista_topic = []
    points = []
    for inst, vec in zip(items, vectors):
        payload = inst.model_dump()
        
        

        

        points.append(PointStruct(id=int(inst.ID), vector=vec, payload=payload))

    upsert_points("similar_proyects", points)

    return {"upserted": len(points)}








