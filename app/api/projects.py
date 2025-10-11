from fastapi import APIRouter, Request
from pydantic import create_model
from typing import List
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from qdrant_client.models import PointStruct
import requests

from app.models.proyecto import Proyecto
from app.services.qdrant_store import upsert_points
from app.services.qdrant_store import search_all_points
from app.services.embeddings_factory import get_embeddings_provider

router = APIRouter(prefix="/projects", tags=["projects"])

# Textualiza los proyectos para vectorizarlos
def _text_of_proyect(p: Proyecto) -> str:
    return ". ".join(filter(None, [
        p.Titulo, p.Descripcion, p.Alcance, p.Area
    ]))

# Textualiza los proyectos en formato de diccionario
def _text_of_proyect_dict(p: dict) -> str:
    return ". ".join(filter(None, [
        p["Titulo"], p["Descripcion"], p["Alcance"], p["Area"]
    ]))

# Carga proyectos historicos desde el BackEnd
def cargar_proyectos_de_backend():
    url = 'https://backend.matchafunding.com/vertodoslosproyectos/'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        return None

# Sube y vectoriza los proyectos del BackEnd
async def subir_proyectos_del_backend(provider):
    proyectos = cargar_proyectos_de_backend()
    texts = list(map(_text_of_proyect_dict, proyectos)) # Optimizar funcion con map()
    vectors = await provider.embed(texts)
    lista_topic = []
    points = []
    for p, vec in zip(proyectos, vectors):
        points.append(PointStruct(id=int(p["ID"]), vector=vec, payload=p))
    upsert_points("similar_proyects", points)

# Sube y vectoriza el proyecto subido por el usuario
@router.post("", summary="Agregar e indexar un solo proyecto")
async def upsert_one_proyect(item: Proyecto, request: Request) -> dict:
    items = [item]
    provider = request.app.state.provider
    texts = list(map(_text_of_proyect, items)) # Optimizar funcion con map()
    vectors = await provider.embed(texts)
    lista_topic = []
    points = []
    for p, vec in zip(items, vectors):
        payload = p.model_dump()
        points.append(PointStruct(id=int(p.ID), vector=vec, payload=payload))
    upsert_points("similar_proyects", points)
    return {"upserted": len(points)}

# Sube y vectoriza multiples proyectos subidos por el usuario
@router.post("/upsert", summary="Agregar e indexar mutiples proyectos")
async def upsert_proyects(items: List[Proyecto], request: Request) -> dict:
    provider = request.app.state.provider
    texts = list(map(_text_of_proyect, items)) # Optimizar funcion con map()
    vectors = await provider.embed(texts)
    lista_topic = []
    points = []
    for p, vec in zip(items, vectors):
        payload = p.model_dump()
        points.append(PointStruct(id=int(p.ID), vector=vec, payload=payload))
    upsert_points("similar_proyects", points)
    return {"upserted": len(points)}

# Muestra todos los proyectos vectorizados
@router.get("/all", summary="Obtener todos los proyectos indexados")
async def get_all_proyects(request: Request) -> dict:
    results, next_page = search_all_points("similar_proyects")    
    proyectos = [item.payload for item in results]
    return {"projects": proyectos}

# Sube y vectoriza multiples proyectos subidos por el usuario
@router.post("/upsertusers", summary="Indexar/actualizar proyectos (batch)")
async def upsert_proyects_users(items: List[Proyecto], request: Request) -> dict:
    provider = request.app.state.provider
    texts = list(map(_text_of_proyect, items)) # Optimizar funcion con map()
    vectors = await provider.embed(texts)
    lista_topic = []
    points = []
    for p, vec in zip(items, vectors):
        payload = p.model_dump()
        points.append(PointStruct(id=int(p.ID), vector=vec, payload=payload))
    upsert_points("user_projects", points)
    return {"upserted": len(points)}
