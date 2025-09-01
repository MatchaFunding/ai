from fastapi import APIRouter, Request
from qdrant_client.models import PointStruct

from app.models.idea import Idea
from app.models.idea_refinada import IdeaRefinada
from app.services.qdrant_store import upsert_points, COL_IDEAS
from app.utils.llm_ollama import llm_generate

router = APIRouter(prefix="/ideas", tags=["ideas"])

PROMPT_TEMPLATE = """
Tu tarea es generar un párrafo describiendo el objetivo general de una idea,
el campo en el que se desarrolla, su descripción, su público objetivo y su factor diferenciador.
No inventes datos. No uses markdown. Emplea un tono profesional y conciso.

<task>
{task}
</task>

Escribe solo el párrafo solicitado.
""".strip()

@router.post("/", response_model=IdeaRefinada, summary="Crea la idea, la refina con LLM, vectoriza y guarda")
async def create_idea(idea: Idea, request: Request) -> IdeaRefinada:
    
    task = (
        f"Sintetiza en 1 párrafo:\n"
        f"- Campo: {idea.Campo}\n"
        f"- Descripción: {idea.Problema}\n"
        f"- Público: {idea.Publico}\n"
        f"- Diferenciador: {idea.Innovacion}"
    )
    prompt = PROMPT_TEMPLATE.format(task=task)

    ## Llamamos a Ollama
    paragraph = await llm_generate(prompt)
    if not paragraph:
        
        paragraph = f"{idea.Campo}. {idea.Problema}. {idea.Publico}. {idea.Innovacion}."

    
    provider = request.app.state.provider
    [embedding] = await provider.embed([paragraph])

    
    point = PointStruct(
        id=int(idea.ID),
        vector=embedding,
        payload={
            "ID": idea.ID,
            "Usuario": idea.Usuario,
            "Campo": idea.Campo,
            "Problema": idea.Problema,
            "Publico": idea.Publico,
            "Innovacion": idea.Innovacion,
            "ResumenLLM": paragraph,   
        },
    )
    upsert_points(COL_IDEAS, [point])

    
    return IdeaRefinada(ID=idea.ID, Usuario=idea.Usuario, ResumenLLM=paragraph)
