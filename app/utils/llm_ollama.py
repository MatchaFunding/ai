import os
import httpx

OLLAMA_HOST  = os.getenv("OLLAMA_HOST", "http://localhost:11434")
#OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4b")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:1b")
GEN_URL = f"{OLLAMA_HOST}/api/generate"

DEFAULT_OPTIONS = {
    "temperature": float(os.getenv("OLLAMA_TEMPERATURE", "1.0")),
    "min_p": float(os.getenv("OLLAMA_MIN_P", "0.01")),
    "repeat_penalty": float(os.getenv("OLLAMA_REPEAT_PENALTY", "1.0")),
    "top_k": int(os.getenv("OLLAMA_TOP_K", "64")),
    "top_p": float(os.getenv("OLLAMA_TOP_P", "0.95")),
}

async def llm_generate(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            GEN_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "options": DEFAULT_OPTIONS},
        )
        r.raise_for_status()
        return (r.json().get("response", "") or "").strip()
