from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional
from qdrant_client.models import PointStruct, Filter
from app.services.qdrant_store import *
import traceback

from app.models.match_result import MatchResult
from app.models.match_request import MatchRequest

router = APIRouter(prefix="/ia", tags=["ia"])

# Funcion auxiliar para ponderar los matchs
def _compute_match_score(topics_match, semantic_match, k:int):
    # Dado que nada asegura que los matchs coincidan, hay que listarlos
    semantic_dict = {int(h.id): h for h in semantic_match}
    topic_dict = {int(h.id): h for h in topics_match}

    # Obtenemos todas las ids: minimo 10, maximo 20
    all_ids = set(semantic_dict) | set(topic_dict)

    final_match: List[MatchResult] = []

    # Recorremos por ID de los Match
    for call_id in all_ids:
        # Obtenemos los scores
        sem = float(semantic_dict.get(call_id).score) if call_id in semantic_dict else 0.0
        top = float(topic_dict.get(call_id).score) if call_id in topic_dict else 0.0

        # Obtenemos los datos segun donde vengan
        payload = (semantic_dict.get(call_id) or topic_dict.get(call_id)).payload or {}
        #Calculamos la afinidad
        affinity = 0.3 * sem + 0.7 * top
        # Agregamos el match a la lista
        final_match.append(MatchResult(
        call_id=call_id,
        name=payload.get("Titulo", "Fondo"),
        agency=str(payload.get("Financiador")) if payload.get("Financiador") else None,
        affinity=affinity,
        semantic_score=sem,
        rules_score=float(0.0),
        topic_score=top,
        explanations=[""]
    ))
    # Ordenamos la lista por afinidad
    final_match.sort(key=lambda x: x.affinity, reverse=True)
    k = min(k, len(final_match))
    # Retornamos los k elementos
    return final_match[:k]

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
    client.get_collection("ideas")
    recs = client.retrieve(
        collection_name="ideas",
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
        
        # Verificar que existe texto para procesar topics
        topics, probs = request.app.state.topic_model.transform(payload['ResumenLLM'])
        vector = probs[0][1:]
        print(f"Vector de topics generado. Dimensión: {len(vector)}")
        
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
        
        print("Buscando matches semánticos...")
        hits = search_funds(idea_vec, top_k=req.top_k, must_filter=qf)
        print(f"Encontrados {len(hits)} matches semánticos")
        
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

# Realiza match entre una idea y los fondos disponibles
@router.get("/{id}/{k}", summary="Dado un id, retorna los k fondos mas asertivos para la idea")
async def match_idea_with_funds(id_idea: int, k: int, request: Request):
    try:
        print(f"Iniciando match para idea ID: {id_idea}")

        # Recolectamos la idea segun la ID
        rec = client.retrieve(
            collection_name="ideas",
            ids = [id_idea],
            with_vectors=True,
            with_payload=True
        )
        
        # Manejo de errores en caso de que no exista la idea
        if not rec: 
            print(f"Error: Idea {id_idea} no encontrada en colección 'ideas'")
            raise HTTPException(status_code=404, detail="Idea no encontrada. Procesa la idea primero.")

        # Recolectamos la idea, su contenido y su vector semantico
        user_idea = rec[0]
        payload = user_idea.payload
        semantic_vector = user_idea.vector
        # Extraemos los vectores de los topicos
        _, probs = request.app.state.topic_model.transform(payload.get('ResumenLLM'))
        topic_vector = probs[0][1:]

        # Si, por alguna razon no hay vector semantico, lo creamos
        if not semantic_vector:
            # Recolectamos el texto con valor semantico
            text = payload.get("ResumenLLM") or " ".join(filter(None, [
                payload.get("Campo"), payload.get("Problema"),
                payload.get("Publico"), payload.get("Innovacion"),
            ])) or ""
            text = text.strip()

            # En caso de no tener vector ni texto, no hay match
            if not text:
                raise HTTPException(status_code=500, detail="Idea almacenada sin vector ni texto para recomputar.")
            
            # Generamos el vector semantico
            provider = request.app.state.provider
            [semantic_vector] = await provider.embed([text])
            # Subimos el vector a la coleccion qdrant
            upsert_points("ideas", [
                PointStruct(id=id_idea, vector=semantic_vector, payload=payload)
            ])

        ########################################
        ### Implementar filtros mas adelante ###
        ########################################

        # Realizamos el match por topicos
        hits_topic = search_topics(topic_vector, top_k=k, must_filter=None)
        # Realizamos el match semantico
        hits_semantic = search_funds(semantic_vector, top_k=k, must_filter=None)
        # Generamos la ponderacion
        response = _compute_match_score(hits_topic, hits_semantic, k)
        # Retornamos
        return response

    # Manejo de errores    
    except Exception as e:
        print(f"Error en match endpoint: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")