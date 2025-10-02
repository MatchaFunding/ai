from fastapi import APIRouter, Request
from qdrant_client.models import PointStruct
from app.models.idea import Idea
from app.models.idea_processed import IdeaProcessed
from app.services.qdrant_store import upsert_points, COL_IDEAS

router = APIRouter(prefix="/ia", tags=["ia"])

@router.post("/process-idea", response_model=IdeaProcessed)
async def process_idea(idea: Idea, request: Request) -> IdeaProcessed:
    provider = request.app.state.provider
    text = f"{idea.Campo}. {idea.Problema}. {idea.Publico}. {idea.Innovacion}."
    [embedding] = await provider.embed([text])

    point = PointStruct(
        id=int(idea.ID),
        vector=embedding,
        payload={
            "ID": idea.ID,
            "Usuario": idea.Usuario,
            "Campo": idea.Campo,
            "Publico": idea.Publico,
            "Problema": idea.Problema,
            "Innovacion": idea.Innovacion,
        }
    )
    upsert_points(COL_IDEAS, [point])

    return IdeaProcessed(
        ID=idea.ID,
        Usuario=idea.Usuario,
        Campo=idea.Campo.strip().lower(),
        Problema=idea.Problema.strip(),
        Publico=idea.Publico.strip(),
        Innovacion=idea.Innovacion.strip(),
        Embedding=embedding,
    )
