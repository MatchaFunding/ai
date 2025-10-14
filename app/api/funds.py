from fastapi import APIRouter, Request, HTTPException
from typing import List
from qdrant_client.models import PointStruct
import requests
import traceback
from app.models.instrumento import Instrumento
from app.services.qdrant_store import upsert_points
from app.services.qdrant_store import search_all_points
from app.services.embeddings_factory import get_embeddings_provider

router = APIRouter(prefix="/funds", tags=["funds"])

# Junta todos los campos de texto del instrumento en un unico String
def _text_of_fund(i: Instrumento) -> str:
    return ". ".join(filter(None, [
        i.Titulo, i.Descripcion, i.Requisitos, i.Beneficios, i.TipoDePerfil
    ]))

# Textualiza los fondos / instrumentos en formato de diccionario
def _text_of_fund_dict(p: dict) -> str:
    return ". ".join(filter(None, [
        p["Titulo"], 
        p["Descripcion"],
        p["Requisitos"],
        p["Beneficios"],
        p["TipoDePerfil"]
    ]))

# Carga instrumentos vigentes y historicos desde el BackEnd
def cargar_instrumentos_de_backend():
    url = 'https://core.matchafunding.com/vertodoslosinstrumentos/'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        return None

# Sube y vectoriza los instrumentos vigentes y historicos desde el BackEnd
async def subir_instrumentos_del_backend(provider, topic_model):
    fondos = cargar_instrumentos_de_backend()
    texts = list(map(_text_of_fund_dict, fondos)) # Optimizar funcion con map()
    vectors = await provider.embed(texts)
    lista_topic = []
    points = []
    for f, vec in zip(fondos, vectors):
        payload = f.copy()
        payload.setdefault("Estado", f['Estado'])
        _, probs = topic_model.transform(f['Descripcion'])
        topicos = probs[0][1:]
        punto = PointStruct(id=int(f["ID"]), vector=topicos, payload=payload)
        lista_topic.append(punto)
        points.append(PointStruct(id=int(f["ID"]), vector=vec, payload=payload))
    upsert_points("funds_topics", lista_topic)
    upsert_points("funds", points)

# Muestra todos los instrumentos vectorizados
@router.get("/all", summary="Obtener todos los instrumentos indexados")
async def get_all_funds(request: Request) -> dict:
    results, next_page = search_all_points("funds")
    fondos = [item.payload for item in results]
    return {"funds": fondos}

# Sube y vectoriza un fondo subido por el usuario
@router.post("/upsert", summary="Agregar e indexar un solo fondo")
async def upsert_funds(items: List[Instrumento], request: Request) -> dict:
    provider = request.app.state.provider
    texts = list(map(_text_of_fund, items)) # Optimizar funcion con map()
    vectors = await provider.embed(texts)
    lista_topic = []
    points = []
    for i, vec in zip(items, vectors):
        payload = i.model_dump()
        payload.setdefault("Estado", i.Estado)
        topics, probs = request.app.state.topic_model.transform(i.Descripcion)
        topicos = probs[0][1:]
        punto = PointStruct(id=int(i.ID), vector=topicos, payload=payload)
        lista_topic.append(punto)
        points.append(PointStruct(id=int(i.ID), vector=vec, payload=payload))
    upsert_points("funds_topics", lista_topic)
    upsert_points("funds", points)
    return {"upserted": len(points)}


