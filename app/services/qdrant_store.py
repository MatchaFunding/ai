import os
from typing import Iterable, List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams, Distance, PointStruct, Filter,
    FieldCondition, MatchValue, MatchAny
)

# Variables de entorno para comunicarse con Qdrant
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

# Numero de topics almacenados en el modelo
NUMBER_OF_TOPICS = os.getenv("NUMBER_OF_TOPICS", 90)

# Se conecta al servicio de Qdrant ya levantado
client = QdrantClient(url=QDRANT_URL)
#client = QdrantClient(":memory:")

# Carga los nuevos elementos en la coleccion
def ensure_collection(name: str, vector_size: int):
    existing = [c.name for c in client.get_collections().collections]
    if name not in existing:
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
	
# Upsertea los puntos hacia la colleccion
def upsert_points(collection: str, points: List[PointStruct]):
    client.upsert(collection_name=collection, points=points)

# Busca la colleccion de instrumentos
def search_funds(
    query_vector: List[float],
    top_k: int = 10,
    must_filter: Filter | None = None
):
    return client.search(
        collection_name="funds",
        query_vector=query_vector,
        limit=top_k,
        query_filter=must_filter
    )

# Busca los topicos en la coleccion
def search_topics(
    query_vector: List[float],
    top_k: int = 10,
    must_filter: Filter | None = None
):
    return client.search(
        collection_name="funds_topics",
        query_vector=query_vector,
        limit=top_k,
        query_filter=must_filter
    )

# Busca los proyectos en la coleccion
def search_projects(
    query_vector: List[float],
    top_k: int = 10,
    must_filter: Filter | None = None
):
    return client.search(
        collection_name="similar_proyects",
        query_vector=query_vector,
        limit=top_k,
        query_filter=must_filter
    )

# Busca todos los puntos en la coleccion
def search_all_points(collection: str):
    return client.scroll(
        collection_name=collection,
        limit=1000,
        with_payload=True,
        with_vectors=True
    )

# Helpers de filtros (region/estado/tipo beneficiario, etc.)
def build_filter(
    estado: str | None = None,
    regiones: list[str] | None = None,
    tipos_perfil: list[str] | None = None,
) -> Filter | None:
    conds = []
    if estado:
        conds.append(FieldCondition(key="Estado", match=MatchValue(value=estado)))
    if regiones:
        conds.append(FieldCondition(key="Regiones", match=MatchAny(any=regiones)))
    if tipos_perfil:
        conds.append(FieldCondition(key="TiposDePerfil", match=MatchAny(any=tipos_perfil)))
    if conds:
        return Filter(must=conds)
    return None
