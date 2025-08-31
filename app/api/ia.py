from fastapi import APIRouter
from app.models.idea import Idea
from app.models.idea_processed import IdeaProcessed
from app.services.embeddings_factory import get_embeddings_provider

router = APIRouter(prefix="/ia", tags=["ia"])
_provider = get_embeddings_provider()

@router.post("/process-idea", response_model=IdeaProcessed)
async def process_idea(idea: Idea) -> IdeaProcessed:
    text = f"{idea.Campo}. {idea.Problema}. {idea.Publico}. {idea.Innovacion}."
    [embedding] = await _provider.embed([text])
    return IdeaProcessed(
        ID=idea.ID,
        Usuario=idea.Usuario,
        Campo=idea.Campo.lower().strip(),
        Problema=idea.Problema.strip(),
        Publico=idea.Publico.strip(),
        Innovacion=idea.Innovacion.strip(),
        Embedding=embedding,
    )
