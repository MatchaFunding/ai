import os
from typing import Iterable, List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams, Distance, PointStruct, Filter,
    FieldCondition, MatchValue, MatchAny
)

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COL_FUNDS  = os.getenv("QDRANT_FUNDS_COLLECTION", "funds")
COL_IDEAS  = os.getenv("QDRANT_IDEAS_COLLECTION", "ideas")
COL_FUNDS_TOPICS = os.getenv("QDRANT_FUNDS_TOPICS_COLLECTION", "funds_topics")
COL_PROYECT_SIMILARITY = os.getenv("QDRANT_SIMILAR_PROYECTS_COLLECTION", "similar_proyects")
NUMBER_OF_TOPICS = os.getenv("NUMBER_OF_TOPICS", 90)



client = QdrantClient(url=QDRANT_URL)

def ensure_collection(name: str, vector_size: int):
    # Crea si no existe (no borra si ya está)
    existing = [c.name for c in client.get_collections().collections]
    if name not in existing:
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

def upsert_points(collection: str, points: List[PointStruct]):
    client.upsert(collection_name=collection, points=points)

def search_funds(
    query_vector: List[float],
    top_k: int = 10,
    must_filter: Filter | None = None
):
    return client.search(
        collection_name=COL_FUNDS,
        query_vector=query_vector,
        limit=top_k,
        query_filter=must_filter
    )


def search_topics(
    query_vector: List[float],
    top_k: int = 10,
    must_filter: Filter | None = None
):
    return client.search(
        collection_name=COL_FUNDS_TOPICS,
        query_vector=query_vector,
        limit=top_k,
        query_filter=must_filter
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
    return Filter(must=conds) if conds else None
