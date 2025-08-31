from fastapi import APIRouter
from app.models.idea import Idea


import json
from enum import Enum
from pathlib import Path
from tqdm import tqdm
import requests
import ollama




# Configuración de Ollama
API = "http://localhost:11434/api/generate"
#MODEL = "llama3.2:latest"

MODEL = "gemma3:4b"
TEMPERATURE = 1.0
MIN_P = 0.01
REPEAT_PENALTY = 1.0
TOP_K = 64
TOP_P = 0.95



def llamar_modelo_local(prompt):
    try:
        resp = requests.post(API, json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options":{
            "temperature": TEMPERATURE,
            "min_p": MIN_P,
            "repeat_penalty": REPEAT_PENALTY,
            "top_k": TOP_K,
            "top_p": TOP_P,
            },
        })
        resp.raise_for_status()
        return resp.json().get("response", "")
    except Exception as e:
        print("Error llamando modelo:", e)
        return ""
    


class ResponseFormat(Enum):
    JSON = "json_object"
    TEXT = "text"














router = APIRouter(prefix="/ideas", tags=["ideas"])

@router.post("/", response_model=Idea, summary="Crear/validar una Idea (echo)")
def create_idea(idea: Idea) -> Idea:


    print(idea)

    """
    Endpoint mínimo para validar contrato de entrada/salida con el modelo Idea.
    Por ahora retorna un eco del payload (sirve para tests y para alinear frontend/backend).
    """
    campo_idea = idea.Campo 
    descripcion_idea = idea.Problema 
    descripcion_publico = idea.Publico
    descripcion_diferenciador = idea.Innovacion

    task = f"""
    Sintetizar la idea de los siguientes campos en un solo parrafo:
    campo de estudio de la idea: {campo_idea}
    descripcion general de la idea: {descripcion_idea}
    publico objetivo de la idea : {descripcion_publico}
    ventaja comparativa de la idea: {descripcion_diferenciador}
    """



    CODING_PROMPT = f"""

    Tu tarea es generar un parrafo describiendo el objetivo general de una idea, el campo en la que se desarrolla, su descripción, su publico objetivo, y su factor diferenciador.
    Estos elementos vendrán como parámetros y tendrás que sintetizarlos de forma seria:
    <task>
    {task}
    </task>

    Sigue las siguientes instrucciones
    1. Escribe un parrafo breve que captura el campo en el que se va a desarrollar la idea. NO USAR MARKDOWN
    2. No inventar cosas que no esten en los parámetros ingresados.
    3. Si tienes información disponible de los procesos de la CORFO y ANID usalos para construir el parrafo más adecuadamente.
    4. No digas explicitamente "factor diferenciador", usa modos del habla distintos como "de distingue las alternativas del mercado haciendo---" 

    Escribe solo el parrafo solicitado
    """

    
    def create_coding_prompt(task: str) -> str:
        return CODING_PROMPT.format(task=task)



    response = llamar_modelo_local(create_coding_prompt(task))
    print(response)









    return idea
