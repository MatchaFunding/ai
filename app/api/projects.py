from fastapi import APIRouter, Request, HTTPException
from pydantic import create_model
from typing import List
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from qdrant_client.models import PointStruct
import requests

from app.models.proyecto import Proyecto
from app.models.user_project import UserProject
from app.models.match_result import MatchResult
from app.services.qdrant_store import upsert_points
from app.services.qdrant_store import search_all_points
from app.services.embeddings_factory import get_embeddings_provider
from app.services.qdrant_store import *

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

# Sube y vectoriza los proyectos del BackEnd
async def subir_proyectos_de_core(provider):
    proyectos = []
    with open('proyectos.json') as json_data:
        proyectos = json.load(json_data)
    texts = list(map(_text_of_proyect_dict, proyectos)) # Optimizar funcion con map()
    vectors = await provider.embed(texts)
    lista_topic = []
    points = []
    for p, vec in zip(proyectos, vectors):
        points.append(PointStruct(id=int(p["ID"]), vector=vec, payload=p))
    upsert_points("similar_projects", points)

# Sube y vectoriza los proyectos del BackEnd
async def subir_proyectos_del_backend(provider):
    proyectos = []
    with open('proyectos.json') as json_data:
        proyectos = json.load(json_data)
    texts = list(map(_text_of_proyect_dict, proyectos)) # Optimizar funcion con map()
    vectors = await provider.embed(texts)
    lista_topic = []
    points = []
    for p, vec in zip(proyectos, vectors):
        points.append(PointStruct(id=int(p["ID"]), vector=vec, payload=p))
    upsert_points("user_projects", points)

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
    upsert_points("similar_projects", points)
    return {"upserted": len(points)}

# Sube y vectoriza multiples proyectos subidos por el usuario
@router.post("/upsert", summary="Agregar e indexar mutiples proyectos")
async def upsert_projects(items: List[Proyecto], request: Request) -> dict:
    provider = request.app.state.provider
    texts = list(map(_text_of_proyect, items)) # Optimizar funcion con map()
    vectors = await provider.embed(texts)
    lista_topic = []
    points = []
    for p, vec in zip(items, vectors):
        payload = p.model_dump()
        points.append(PointStruct(id=int(p.ID), vector=vec, payload=payload))
    upsert_points("similar_projects", points)
    return {"upserted": len(points)}

# Muestra todos los proyectos vectorizados
@router.get("/all", summary="Obtener todos los proyectos indexados")
async def get_all_projects(request: Request) -> dict:
    results, next_page = search_all_points("similar_projects")
    proyectos = [item.payload for item in results]
    return {"projects": proyectos}

# Sube y vectoriza multiples proyectos subidos por el usuario
@router.post("/upsertusers", summary="Indexar/actualizar proyectos (batch)")
async def upsert_projects_users(items: List[Proyecto], request: Request) -> dict:
    provider = request.app.state.provider
    texts = list(map(_text_of_proyect, items)) # Optimizar funcion con map()
    vectors = await provider.embed(texts)
    lista_topic = []
    points = []
    for p, vec in zip(items, vectors):
        payload = p.model_dump()

        # if vec == None:
        #     [vec] = await provider.embed([payload.Descripcion])

        points.append(PointStruct(
            id=int(p.ID),
            vector=vec,
            payload=payload))
    upsert_points("user_projects", points)
    return {"upserted": len(points)}

# Realiza el match entre un proyecto de usuario subido previamente a Qdrant
@router.get("/user-projects/{id_project}/matches", summary="Retorna los proyectos históricos más similares al del usuario")
async def match_user_projects_with_historical_projects(id_project: int, request: Request):
    # Buscamos el proyecto en Qdrant
    rec = client.retrieve(
        collection_name="user_projects",
        ids=[id_project],
        with_vectors=True,
        with_payload=True
    )
    if not rec:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado. Procesa el proyecto primero.")
    # Obtenemos los vectores
    projectFromQdrant = rec[0]
    projectVector = projectFromQdrant.vector
    # Realizamos el match semántico
    hits = search_projects(projectVector)
    # Preparamos el retorno
    out: List[MatchResult] = []
    for h in hits:
        payload = h.payload or {}
        semantic = float(h.score)
        affinity = semantic
        out.append(MatchResult(
            call_id=int(h.id),
            name=payload.get("Titulo", "Descripcion"),
            agency=str(payload.get("Area")) if payload.get("Area") is not None else None,
            affinity=affinity,
            semantic_score=semantic,
            rules_score= 0 ,
            explanations=[],
            topic_score=0
        ))
    
    # Ordenamos por afinidad
    out.sort(key=lambda x: x.affinity, reverse=True)
    return out

@router.get("/all-user-projects", summary="Obtener todos los proyectos de usuarioes indexados")
async def get_all_projects(request: Request) -> dict:
    results, next_page = search_all_points("user_projects")
    proyectos = [item.payload for item in results]
    return {"user_projects": proyectos}

# Sección de pruebas: Funciona solo si el archivo se ejecuta como script
if __name__ == "__main__":
    docs = cargar_proyectos_de_backend()
    for i in docs:
        print(i)
