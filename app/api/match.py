from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional
from qdrant_client.models import PointStruct, Filter
from app.services.qdrant_store import (
    COL_IDEAS, COL_FUNDS, client, search_funds, build_filter, upsert_points, 
)
from pathlib import Path
from app.services.embeddings_factory import get_embeddings_provider
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer



topic_model = BERTopic.load("ayuda", embedding_model = get_embeddings_provider())




router = APIRouter(prefix="/ia", tags=["ia"])

class MatchRequest(BaseModel):
    idea_id: int = Field(..., description="ID de la idea ya procesada y guardada en Qdrant")
    top_k: int = 10
    estado: Optional[str] = "abierto"
    regiones: Optional[List[str]] = None
    tipos_perfil: Optional[List[str]] = None

class MatchResult(BaseModel):
    call_id: int
    name: str
    agency: Optional[str] = None
    affinity: float
    semantic_score: float
    rules_score: float
    topic_score: float 
    explanations: List[str] = []

def _rules_score(payload: dict, req: MatchRequest) -> tuple[float, List[str]]:
    score = 1.0
    notes: List[str] = []
    if req.regiones:
        regiones_fondo = set(payload.get("Regiones", []))
        if regiones_fondo and regiones_fondo.isdisjoint(set(req.regiones)):
            score -= 0.6; notes.append("Región preferente no coincide")
    if req.tipos_perfil:
        perfiles = set(payload.get("TiposDePerfil", []))
        if perfiles and perfiles.isdisjoint(set(req.tipos_perfil)):
            score -= 0.4; notes.append("Tipo de perfil no coincide")
    return max(0.0, min(score, 1.0)), notes





'''
MATCH IDEA LABEL

RECIBE LA IDEA CON SU PARRAFO

PROCESA EL PARRAFO Y RETORNA MATCH
'''
@router.post("/topics/", response_model=List[MatchRequest], summary="RECIBE LA IDEA CON SU PARRAFO PROCESA EL PARRAFO Y RETORNA CON FONDOS")
async def match_idea_label(idearef: MatchRequest, k: int = 10):

    recs = client.retrieve(
        collection_name=COL_IDEAS,
        ids=[req.idea_id],
        with_vectors=True,
        with_payload=True,
    )
    if not recs:
        raise HTTPException(status_code=404, detail="Idea no encontrada. Procesa la idea primero.")

    idea_rec = recs[0]
    

    topics, probs = topic_model.transform(idea_rec.paragraph)
    vector = probs[0][1:]





    hits = search_topics(idea_vec, top_k=req.top_k, must_filter=None)
    out: List[MatchResult] = []
    for h in hits:
        payload = h.payload or {}
        
        topic = float(h.score)
        affinity = 0.75 * topic
        out.append(MatchResult(
            call_id=int(h.id),
            name=payload.get("Titulo", "Fondo"),
            agency=str(payload.get("Financiador")) if payload.get("Financiador") is not None else None,
            affinity=affinity,
            semantic_score=semantic,
            rules_score=rules,
            explanations=notes,
        ))
    out.sort(key=lambda x: x.affinity, reverse=True)
    return out

















@router.post("/match", response_model=List[MatchResult])
async def match(req: MatchRequest, request: Request):
    
    recs = client.retrieve(
        collection_name=COL_IDEAS,
        ids=[req.idea_id],
        with_vectors=True,
        with_payload=True,
    )
    if not recs:
        raise HTTPException(status_code=404, detail="Idea no encontrada. Procesa la idea primero.")

    idea_rec = recs[0]
    idea_vec = idea_rec.vector

    
    if not idea_vec:
        payload = idea_rec.payload or {}
        text = payload.get("ResumenLLM") or " ".join(filter(None, [
            payload.get("Campo"), payload.get("Problema"),
            payload.get("Publico"), payload.get("Innovacion"),
        ])) or ""
        text = text.strip()
        if not text:
            raise HTTPException(status_code=500, detail="Idea almacenada sin vector ni texto para recomputar.")

        provider = request.app.state.provider
        [idea_vec] = await provider.embed([text])

        upsert_points(COL_IDEAS, [
            PointStruct(id=int(req.idea_id), vector=idea_vec, payload=payload)
        ])

    
    qf: Filter | None = build_filter(
        estado=req.estado,
        regiones=req.regiones,
        tipos_perfil=req.tipos_perfil
    )

    
    hits = search_funds(idea_vec, top_k=req.top_k, must_filter=qf)
    out: List[MatchResult] = []
    for h in hits:
        payload = h.payload or {}
        rules, notes = _rules_score(payload, req)
        semantic = float(h.score)
        affinity = 0.75 * semantic + 0.25 * rules
        out.append(MatchResult(
            call_id=int(h.id),
            name=payload.get("Titulo", "Fondo"),
            agency=str(payload.get("Financiador")) if payload.get("Financiador") is not None else None,
            affinity=affinity,
            semantic_score=semantic,
            rules_score=rules,
            explanations=notes,
        ))
    out.sort(key=lambda x: x.affinity, reverse=True)
    return out
