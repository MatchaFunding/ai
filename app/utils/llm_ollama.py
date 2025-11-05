import os
import httpx

OLLAMA_HOST  = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4b")
#OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:1b")


# 1. URL de la API de OpenAI
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

# 2. Clave de API (¡Importante! Cárgala desde tus variables de entorno)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise EnvironmentError("La variable de entorno OPENAI_API_KEY no está configurada.")

# 3. Modelo de OpenAI que deseas usar (puedes usar tu ID de modelo fine-tuned aquí)
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "ft:gpt-4.1-nano-2025-04-14:matchafunding:matcha4:CXdSGLE4")

# 4. Prompt del Sistema (basado en nuestro historial de chat)
SYSTEM_PROMPT = "Eres un asistente experto en la formulación y redacción de proyectos. Tu tarea es generar las secciones solicitadas de forma clara y profesional."

# 5. Opciones de payload compatibles con OpenAI
# Mapeamos 'repeat_penalty' a 'frequency_penalty' que es el análogo más cercano
DEFAULT_PAYLOAD_OPTIONS = {
    "temperature": float(os.getenv("OLLAMA_TEMPERATURE", "1.0")),
    "top_p": float(os.getenv("OLLAMA_TOP_P", "0.95")),
    "frequency_penalty": float(os.getenv("OLLAMA_REPEAT_PENALTY", "1.0")),
    # 'top_k' y 'min_p' no son parámetros comunes en la API de Chat Completions
}

async def llm_generate(prompt: str) -> str:
    """
    Envía un prompt a la API de OpenAI Chat Completions y devuelve la respuesta.
    """
    
    # Cabecera de autenticación para OpenAI
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Payload en el formato de OpenAI (Chat Completions)
    json_data = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        **DEFAULT_PAYLOAD_OPTIONS # Expande las opciones de temperatura, top_p, etc.
    }
    
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            r = await client.post(
                OPENAI_API_URL,
                json=json_data,
                headers=headers
            )
            
            # Lanzará un error si la API devuelve 4xx o 5xx
            r.raise_for_status() 
            
            response_json = r.json()
            
            # 6. Parseo de la respuesta de OpenAI
            # La respuesta está anidada dentro de choices[0].message.content
            content = response_json.get("choices", [{}])[0].get("message", {}).get("content", "")
            return content.strip()

        except httpx.HTTPStatusError as e:
            print(f"Error en la solicitud a la API: {e.response.status_code}")
            print(f"Detalle: {e.response.text}")
            return f"Error: {e.response.text}"
        except Exception as e:
            print(f"Ocurrió un error inesperado: {e}")
            return f"Error: {str(e)}"