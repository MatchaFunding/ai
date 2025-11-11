from fastapi import APIRouter, Request
from qdrant_client.models import PointStruct
import requests
import json

from app.models.idea import Idea
from app.models.instrumento import Instrumento
from app.models.idea_refinada import IdeaRefinada
from app.services.qdrant_store import upsert_points
from app.services.qdrant_store import search_all_points
from app.utils.llm_ollama import llm_generate

router = APIRouter(prefix="/ideas", tags=["ideas"])

PROMPT_TEMPLATE = """
Tu tarea es generar un párrafo describiendo el objetivo general de una idea,
el campo en el que se desarrolla, su descripción, su público objetivo y su factor diferenciador.
No inventes datos. No uses markdown. Emplea un tono profesional y conciso.

<task>
{task}
</task>

Sigue las siguientes instrucciones
1. Escribe un parrafo breve que captura el campo en el que se va a desarrollar la idea. NO USAR MARKDOWN
2. No inventar cosas que no esten en los parámetros ingresados.
3. Si tienes información disponible de los procesos de la CORFO y ANID usalos para construir el parrafo más adecuadamente.
4. No digas explicitamente "factor diferenciador", usa modos del habla distintos como "de distingue las alternativas del mercado haciendo---" tampoco menciones directamente a CORFO y ANID
""".strip()

# Sube y vectoriza las ideas de usuarios desde el BackEnd
async def subir_ideas_del_backend(provider):
    ideas = []
    with open('ideas.json') as json_data:
        ideas = json.load(json_data)
    puntos = []
    for i in range(len(ideas)):
        ideas[i]["ResumenLLM"] = ideas[i].pop("Propuesta")
    for idea in ideas:
        paragraph = f"{idea["Campo"]}. {idea["Problema"]}. {idea["Publico"]}. {idea["Innovacion"]}."
        [embedding] = await provider.embed([paragraph])
        punto = PointStruct(
            id=int(idea["ID"]),
            vector=embedding,
            payload={
                "ID": idea["ID"],
                "Usuario": idea["Usuario"],
                "Campo": idea["Campo"],
                "Problema": idea["Problema"],
                "Publico": idea["Publico"],
                "Innovacion": idea["Innovacion"],
                "ResumenLLM": idea["ResumenLLM"],
            },
        )
        puntos.append(punto)
    upsert_points("ideas", puntos)


# Crea una idea para un proyecto usando Ollama, la vectoriza y la guarda en Qdrant
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
    # Llamamos a Ollama
    paragraph = await llm_generate(prompt)
    if not paragraph:
        paragraph = f"{idea.Campo}. {idea.Problema}. {idea.Publico}. {idea.Innovacion}."
    # Carga los datos en Qdrant
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
    upsert_points("ideas", [point])
    return IdeaRefinada(ID=idea.ID, Usuario=idea.Usuario, ResumenLLM=paragraph)

# Muestra todas las ideas de usuarios vectorizados
@router.get("/all", summary="Obtener todas las ideas indexadas")
async def get_all_ideas(request: Request) -> dict:
    results, _ = search_all_points("ideas")
    ideas = [item.payload for item in results]
    return {"ideas": ideas}

# Carga las etiquetas un instrumentos
def carga_labels_instrumento(instrumento: Instrumento, topicos: list):
    payload = fondo.dict()
    payload["uuid"] = str(uuid4())
    if len(topicos)==0:
        topics, probs = topic_model.transform(payload["Descripcion"])
        topicos = probs[0][1:]
    client.upsert(
        collection_name="topic_vectors",
        points=[
            PointStruct(
                id=payload["uuid"],
                vector=topicos,
                payload=payload
            )
        ]
    )
