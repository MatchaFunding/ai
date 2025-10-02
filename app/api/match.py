from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional
from qdrant_client.models import PointStruct, Filter
from app.services.qdrant_store import *

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
@router.post("/topics/", response_model=List[MatchResult], summary="RECIBE LA IDEA CON SU PARRAFO PROCESA EL PARRAFO Y RETORNA CON FONDOS")
async def match_idea_label(req: MatchRequest, request: Request, k: int = 10):
    client.get_collection(COL_IDEAS)
    recs = client.retrieve(
        collection_name=COL_IDEAS,
        ids=[req.idea_id],
        with_vectors=True,
        with_payload=True,
    )
    if not recs:
        raise HTTPException(status_code=404, detail="Idea no encontrada. Procesa la idea primero.")
    idea_rec = recs[0]
    payload = idea_rec.payload
    print(payload)
    topics, probs = request.app.state.topic_model.transform(payload['ResumenLLM'])
    vector = probs[0][1:]
    print(vector)
    #print("suicidio1")
    hits = search_topics(vector, top_k=req.top_k, must_filter=None)
    #print("suicidio2")
    out: List[MatchResult] = []
    #print("suicidio3")
    for h in hits:
        payload = h.payload or {}
        topic = float(h.score)
        affinity = 0.75 * topic
        out.append(MatchResult(
            call_id=int(h.id),
            name=payload.get("Titulo", "Fondo"),
            agency=str(payload.get("Financiador")) if payload.get("Financiador") is not None else None,
            affinity=affinity,
            semantic_score=0,
            rules_score=0,
            topic_score= affinity, 
            explanations=[],
        ))
    print("suicidio4")
    out.sort(key=lambda x: x.affinity, reverse=True)
    return out

'''
HITS TOPIC Y HITS SEMANTICA PROBABLEMENTE DEVUELVEN LOS OBJETOS EN ORDEN DISTINTO

SE DEBE PRIMERO OBTENER TOP 10 DE UNA DE LAS BUSQUEDAS Y CALCULAR LA SIMILITUD VECTORIAL PARA CADA H RESULTANTE

RESOLVER EL PROXIMO SPRINT

'''
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
    payload = idea_rec.payload
    #print(payload)
    topics, probs = request.app.state.topic_model.transform(payload['ResumenLLM'])
    vector = probs[0][1:]
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
    hits_topic = search_topics(vector, top_k=req.top_k, must_filter=None)
    hits = search_funds(idea_vec, top_k=req.top_k, must_filter=qf)
    out: List[MatchResult] = []
    for h_topic, h in zip(hits_topic, hits):
        payload = h.payload or {}
        rules, notes = _rules_score(payload, req)
        semantic = float(h.score)
        topic = float(h_topic.score)
        affinity = 0.20 * semantic + 0.25 * rules + 0.55*topic
        out.append(MatchResult(
            call_id=int(h.id),
            name=payload.get("Titulo", "Fondo"),
            agency=str(payload.get("Financiador")) if payload.get("Financiador") is not None else None,
            affinity=affinity,
            semantic_score=semantic,
            rules_score=rules,
            explanations=notes,
            topic_score=topic
        ))
    out.sort(key=lambda x: x.affinity, reverse=True)
    return out

@router.post("/match/projectmatch", response_model=List[MatchResult])
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
    hits = search_projects(idea_vec, top_k=req.top_k, must_filter=None)
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
    out.sort(key=lambda x: x.affinity, reverse=True)
    return out

@router.post("/match/projectmatchhistoric", response_model=List[MatchResult])
async def match(req: MatchRequest, request: Request):
    recs = client.retrieve(
        collection_name="user_projects",
        ids=[req.idea_id],
        with_vectors=True,
        with_payload=True,
    )
    if not recs:
        raise HTTPException(status_code=404, detail="Idea no encontrada. Procesa la idea primero.")
    idea_rec = recs[0]
    idea_vec = idea_rec.vector
    hits = search_projects(idea_vec, top_k=req.top_k, must_filter=None)
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
    out.sort(key=lambda x: x.affinity, reverse=True)
    return out
