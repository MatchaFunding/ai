from fastapi import APIRouter
from pydantic import BaseModel
from app.utils.llm_ollama import llm_generate

router = APIRouter(prefix="/rag", tags=["rag"])

# Modelo para recibir la pregunta del usuario
class QuestionRequest(BaseModel):
    question: str
    fondo_nombre: str = None  # Nombre del fondo para contexto (opcional)

# Modelo para la respuesta
class AnswerResponse(BaseModel):
    answer: str
    fondo: str = None

# Prompt template para el chatbot RAG (mockup)
RAG_PROMPT_TEMPLATE = """
Eres un asistente experto en fondos de financiamiento chilenos (CORFO, ANID, etc.).
Tu tarea es responder preguntas de usuarios sobre fondos de financiamiento de manera clara, 
profesional y útil.

Responde de manera concisa y directa. No uses markdown en tu respuesta.
Si no tienes información específica, proporciona una respuesta general útil basada 
en tu conocimiento de fondos de financiamiento.

Pregunta del usuario: {question}

{fondo_context}

Responde de manera clara y profesional:
""".strip()

@router.post("/chat", response_model=AnswerResponse, summary="Procesar pregunta del chat RAG")
async def rag_chat(request: QuestionRequest) -> AnswerResponse:
    """
    Endpoint para procesar preguntas del usuario en el chat RAG.
    Por ahora usa Ollama con un prompt simple (mockup).
    
    Args:
        request: Objeto con la pregunta y opcionalmente el nombre del fondo
        
    Returns:
        Respuesta generada por el LLM
    """
    # Construir contexto si hay nombre de fondo
    fondo_context = ""
    if request.fondo_nombre:
        fondo_context = f"Contexto: El usuario está preguntando sobre el fondo '{request.fondo_nombre}'."
    
    # Crear el prompt
    prompt = RAG_PROMPT_TEMPLATE.format(
        question=request.question,
        fondo_context=fondo_context
    )
    
    # Llamar a Ollama
    answer = await llm_generate(prompt)
    
    # Si no hay respuesta, usar un mensaje por defecto
    if not answer:
        answer = "Lo siento, no pude procesar tu pregunta en este momento. Por favor intenta de nuevo."
    
    return AnswerResponse(
        answer=answer,
        fondo=request.fondo_nombre
    )

@router.get("/health", summary="Verificar estado del servicio RAG")
async def health_check():
    """Endpoint simple para verificar que el servicio está funcionando"""
    return {"status": "ok", "service": "rag-chat"}
