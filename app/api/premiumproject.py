from fastapi import APIRouter, Request
from qdrant_client.models import PointStruct
import requests

from app.models.idea import Idea
from app.models.instrumento import Instrumento
from app.models.idea_refinada import IdeaRefinada
from app.services.qdrant_store import upsert_points
from app.services.qdrant_store import search_all_points
from app.utils.llm_ollama import llm_generate

router = APIRouter(prefix="/premium", tags=["premium"])

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







PROMPT_TEMPLATE_PROBLEMA = """
Tu tarea es generar uno o dos párrafos describiendo el problema principal que busca resolver un proyecto. Se te va a proveer de datos iniciales para desarrollar tu resultado.
Señale claramente cuál es el problema u oportunidad a abordar y hacia el(la) cual se dirige la solución propuesta, identificando a los actores a los que afecta este problema o se verían beneficiados con esta oportunidad. Fundamente su relevancia y vigencia científica tecnológica. Acote la dimensión del problema a los aspectos específicos que se busca enfrentar con el proyecto.
No inventes datos. No uses markdown. Emplea un tono profesional y conciso.
<task>
{task}
</task>


""".strip()



PROMPT_TEMPLATE_SOLUCION = """
Tu tarea es generar uno o dos párrafos describiendo la solución que se busca alcanzar para el problema principal de un proyecto.  Se te va a proveer de datos iniciales para desarrollar tu resultado.

Describa de manera clara y precisa la solución que busca alcanzar y que resuelva el problema/oportunidad que el proyecto pretende abordar e identificada en la sección anterior. Considere la solución que será dispuesta al usuario final y/o intermedio o al receptor de esta. Incluya su definición, condiciones de uso, indicadores de desempeño esperados, principales atributos diferenciadores, entre otros aspectos que agreguen valor y que la diferencian de soluciones alternativas y/o sustitutos en desarrollo o que están disponibles actualmente.

No inventes datos. No uses markdown. Emplea un tono profesional y conciso.

<task>
{task}
</task>


""".strip()



PROMPT_TEMPLATE_PUBOB = """
Tu tarea es generar uno o dos parrafos caracterizando el mercado y publico objetivo. Se te va a proveer de datos iniciales para desarrollar tu resultado.

Considerando a los actores a los que afecta el problema o se verían beneficiados con la oportunidad  caracterice el mercado potencial y objetivo hacia el cual está dirigido el producto, proceso y/o servicio (solución final). Lo anterior requiere establecer adecuadamente cuáles son los segmentos del mercado que se podrían atender con la solución propuesta (solución final). 
Sobre este conjunto de usuarios/beneficiarios describa el potencial impacto en términos económicos, sociales, ambientales y territoriales, que derivarían por el uso o adopción del producto, proceso y/o servicio (solución final).
Para proyectos que producen un bien público en la forma de producto, proceso y/o servicio, considerando que el propósito es ir en beneficio de la comunidad chilena o de algún sector de ella a través de entidades públicas u organismos sin fines de lucro, identifique los usuarios o beneficiarios finales, haciendo énfasis en el impacto que generaría en ellos la aplicación del producto, proceso y/o servicio que se busca alcanzar (solución final).  



No inventes datos. No uses markdown. Emplea un tono profesional y conciso.

<task>
{task}
</task>


""".strip()



PROMPT_TEMPLATE_OBJETIVO_ESPECIFICO = """
Tu tarea es generar un párrafo describiendo los objetivos especificos de una idea. Se te va a proveer de datos iniciales para desarrollar tu resultado.
Agregue los objetivos específicos necesarios (máximo 5). Estos deben estar contenidos en el objetivo general. 

No inventes datos. No uses markdown. Emplea un tono profesional y conciso.

<task>
{task}
</task>


""".strip()



PROMPT_TEMPLATE_OBJETIVO_GENERAL = """
Tu tarea es generar uno o dos párrafos describiendo el objetivo general de una idea. Se te va a proveer de datos iniciales para desarrollar tu resultado. 

Sea preciso(a) al formular este objetivo, el cual debe conducir al logro del(los) resultado(s) tecnológico(s) propuesto(s).

<task>
{task}
</task>

No inventes datos. No uses markdown. Emplea un tono profesional y conciso.

<task>
{task}
</task>


""".strip()






PROMPT_TEMPLATE_RESULTADO_ESPERADO = """
Tu tarea es generar uno o dos párrafos describiendo  los resultados esperados de la idea. Se te va a proveer de datos iniciales para desarrollar tu resultado. 
Describa el o los resultados tecnológicos que espera lograr (señalar como máximo 2), poniendo énfasis en el nivel de desarrollo que se alcanzará al finalizar esta propuesta. 
El resultado tecnológico corresponde a prototipos de tecnologías/conjunto de conocimientos en la forma de productos, procesos y/o servicios nuevos y/o mejorados, con base en investigación aplicada y desarrollo experimental, y que está estrechamente relacionado con la solución final que resuelve/aborda el problema/oportunidad detectada. Los prototipos o conjunto de conocimientos deben lograr un avance en la madurez tecnológica respecto de la situación al inicio del proyecto.


No inventes datos. No uses markdown. Emplea un tono profesional y conciso.

<task>
{task}
</task>


""".strip()









# Crea una idea para un proyecto usando Ollama, la vectoriza y la guarda en Qdrant


@router.post("/problema", response_model=IdeaRefinada, summary="Crea la idea, la refina con LLM, vectoriza y guarda")
async def create_idea(idea: Idea, request: Request) -> IdeaRefinada:
    task = (
        f"Sintetiza en 1-2 párrafos:\n"
        f"- Campo: {idea.Campo}\n"
        f"- Descripción: {idea.Problema}\n"
        f"- Público: {idea.Publico}\n"
        
    )
    prompt = PROMPT_TEMPLATE_PROBLEMA.format(task=task)
    # Llamamos a Ollama
    paragraph = await llm_generate(prompt)
    if not paragraph:
        paragraph = f"{idea.Campo}. {idea.Problema}. {idea.Publico}. {idea.Innovacion}."
    
    return IdeaRefinada(ID=idea.ID, Usuario=idea.Usuario, ResumenLLM=paragraph)

@router.post("/solucion", response_model=IdeaRefinada, summary="Crea la idea, la refina con LLM, vectoriza y guarda")
async def create_idea(idea: Idea, request: Request) -> IdeaRefinada:
    task = (
        f"Sintetiza en 1-2 párrafos la solucion con los siguientes campos:\n"
        f"- Campo: {idea.Campo}\n"
        f"- Descripción del problema. NO INCLUIR DIRECTAMENTE, SE DESARROLLO EN UN PARRAFO ANTERIOR: {idea.Problema}\n"
        f"- Público: {idea.Publico}\n"
        f"- Inovacion: {idea.Innovacion}\n"
    )
    prompt = PROMPT_TEMPLATE_SOLUCION.format(task=task)
    # Llamamos a Ollama
    paragraph = await llm_generate(prompt)
    if not paragraph:
        paragraph = f"{idea.Campo}. {idea.Problema}. {idea.Publico}. {idea.Innovacion}."
    
    return IdeaRefinada(ID=idea.ID, Usuario=idea.Usuario, ResumenLLM=paragraph)

@router.post("/pubob", response_model=IdeaRefinada, summary="Crea la idea, la refina con LLM, vectoriza y guarda")
async def create_idea(idea: Idea, request: Request) -> IdeaRefinada:
    task = (
        f"Sintetiza en 1-2 párrafos el publico objetivo del problema con los siguientes campos:\n"
        f"- Campo: {idea.Campo}\n"
        f"- Descripción del problema. NO INCLUIR DIRECTAMENTE, SE DESARROLLO EN UN PARRAFO ANTERIOR: {idea.Problema}\n"
        f"- Público: {idea.Publico}\n"
        f"- Inovacion, NO INCLUIR DIRECTAMENTE, SE DESARROLLO EN UN PARRAFO ANTERIOR: {idea.Innovacion}\n"
    )
    prompt = PROMPT_TEMPLATE_PUBOB.format(task=task)
    # Llamamos a Ollama
    paragraph = await llm_generate(prompt)
    if not paragraph:
        paragraph = f"{idea.Campo}. {idea.Problema}. {idea.Publico}. {idea.Innovacion}."
    
    return IdeaRefinada(ID=idea.ID, Usuario=idea.Usuario, ResumenLLM=paragraph)


@router.post("/Obgen", response_model=IdeaRefinada, summary="Crea la idea, la refina con LLM, vectoriza y guarda")
async def create_idea(idea: Idea, request: Request) -> IdeaRefinada:
    task = (
        f"Sintetiza en 1 solo párrafo el objetivo general del problema. Se breve:\n"
        f"- Campo: {idea.Campo}\n"
        f"- Descripción del problema. NO INCLUIR DIRECTAMENTE, SE DESARROLLO EN UN PARRAFO ANTERIOR: {idea.Problema}\n"
        f"- Público: {idea.Publico}\n"
        f"- Inovacion: {idea.Innovacion}\n"
    )
    prompt = PROMPT_TEMPLATE_OBJETIVO_GENERAL.format(task=task)
    # Llamamos a Ollama
    paragraph = await llm_generate(prompt)
    if not paragraph:
        paragraph = f"{idea.Campo}. {idea.Problema}. {idea.Publico}. {idea.Innovacion}."
    
    return IdeaRefinada(ID=idea.ID, Usuario=idea.Usuario, ResumenLLM=paragraph)



@router.post("/Obes", response_model=IdeaRefinada, summary="Crea la idea, la refina con LLM, vectoriza y guarda")
async def create_idea(idea: Idea, request: Request) -> IdeaRefinada:
    task = (
        f"Enumera en un solo  párrafo los objetivos especificos de un proyecto segun las siguientes variables:\n"
        f"- Campo: {idea.Campo}\n"
        f"- Descripción del problema. NO INCLUIR DIRECTAMENTE, SE DESARROLLO EN UN PARRAFO ANTERIOR: {idea.Problema}\n"
        f"- Público: {idea.Publico}\n"
        f"- Inovacion: {idea.Innovacion}\n"
    )
    prompt = PROMPT_TEMPLATE_OBJETIVO_ESPECIFICO.format(task=task)
    # Llamamos a Ollama
    paragraph = await llm_generate(prompt)
    if not paragraph:
        paragraph = f"{idea.Campo}. {idea.Problema}. {idea.Publico}. {idea.Innovacion}."
    
    return IdeaRefinada(ID=idea.ID, Usuario=idea.Usuario, ResumenLLM=paragraph)



@router.post("/resultado", response_model=IdeaRefinada, summary="Crea la idea, la refina con LLM, vectoriza y guarda")
async def create_idea(idea: Idea, request: Request) -> IdeaRefinada:
    task = (
        f"Sintetiza en 1-2 párrafos El resultado esperado de un proyecto con la siguiente informacion:\n"
        f"- Campo: {idea.Campo}\n"
        f"- Descripción del problema. NO INCLUIR DIRECTAMENTE, SE DESARROLLO EN UN PARRAFO ANTERIOR: {idea.Problema}\n"
        f"- Público: {idea.Publico}\n"
        f"- Inovacion: {idea.Innovacion}\n"
    )
    prompt = PROMPT_TEMPLATE_RESULTADO_ESPERADO.format(task=task)
    # Llamamos a Ollama
    paragraph = await llm_generate(prompt)
    if not paragraph:
        paragraph = f"{idea.Campo}. {idea.Problema}. {idea.Publico}. {idea.Innovacion}."
    
    return IdeaRefinada(ID=idea.ID, Usuario=idea.Usuario, ResumenLLM=paragraph)



