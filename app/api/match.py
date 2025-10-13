from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional
from qdrant_client.models import PointStruct, Filter
from app.services.qdrant_store import *
import traceback

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
Recibe el ID de una Idea subida por algun Usuario y luego obtiene los MatchResult
mas similares en un arreglo
'''
@router.post("/match", response_model=List[MatchResult])
async def match(req: MatchRequest, request: Request):
    try:
        print(f"Iniciando match para idea ID: {req.idea_id}")
        recs = client.retrieve(
            collection_name="ideas",
            ids=[req.idea_id],
            with_vectors=True,
            with_payload=True,
        )
        if not recs:
            print(f"Error: Idea {req.idea_id} no encontrada en colección 'ideas'")
            raise HTTPException(status_code=404, detail="Idea no encontrada. Procesa la idea primero.")
        idea_rec = recs[0]
        payload = idea_rec.payload
        print(f"Idea encontrada. Payload: {payload}")
        topics, probs = request.app.state.topic_model.transform(payload['ResumenLLM'])
        vector = probs[0][1:]
        print(f"Vector de topics generado. Dimensión: {len(vector)}")
        print(f"Vector de topicos generado: {vector}")
        idea_vec = idea_rec.vector
        if not idea_vec:
            print("Generando vector de idea...")
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
            upsert_points("ideas", [
                PointStruct(id=int(req.idea_id), vector=idea_vec, payload=payload)
            ])
        
        qf: Filter | None = build_filter(
            estado=req.estado,
            regiones=req.regiones,
            tipos_perfil=req.tipos_perfil
        )
        
        print("Buscando matches por topics...")
        hits_topic = search_topics(vector, top_k=req.top_k, must_filter=None)
        print(f"Encontrados {len(hits_topic)} matches por topics")
        print(f"Matches por topico:\n{hits_topic}")
        
        print("Buscando matches semánticos...")
        hits = search_funds(idea_vec, top_k=req.top_k, must_filter=qf)
        print(f"Encontrados {len(hits)} matches semánticos")
        print(f"Matches semanticos:\n{hits_topic}")
        
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
        print(f"Retornando {len(out)} matches ordenados")
        return out
        
    except Exception as e:
        print(f"Error en match endpoint: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/health/collections")
async def check_collections():
    """Endpoint para verificar el estado de las colecciones"""
    try:
        ideas_scroll = client.scroll("ideas", limit=1000)
        ideas_count = len(ideas_scroll[0])
        
        funds_scroll = client.scroll("funds", limit=1000)
        funds_count = len(funds_scroll[0])
        
        funds_topics_scroll = client.scroll("funds_topics", limit=1000)
        funds_topics_count = len(funds_topics_scroll[0])
        
        return {
            "status": "ok",
            "collections": {
                "ideas": ideas_count,
                "funds": funds_count,
                "funds_topics": funds_topics_count
            }
        }
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e),
            "collections": {
                "ideas": "unknown",
                "funds": "unknown", 
                "funds_topics": "unknown"
            }
        }

@router.post("/match/projectmatch", response_model=List[MatchResult])
async def match(req: MatchRequest, request: Request):
    recs = client.retrieve(
        collection_name="ideas",
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
