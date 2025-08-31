from fastapi import FastAPI
from datetime import datetime, timezone

from app.api import ideas
from app.api import ia
from fastapi.middleware.cors import CORSMiddleware





app = FastAPI(title="IA Service", version="0.1.0")
API_PREFIX = "/api/v1"

@app.get(f"{API_PREFIX}/health")
def health():
    return {
        "status": "ok",
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "version": app.version,
        "service": app.title,
    }


# Aquí defines desde qué orígenes aceptarás peticiones
origins = [
    "http://localhost:5173",  # tu frontend local
    "http://127.0.0.1:5173",
    # puedes agregar más dominios aquí
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # qué orígenes aceptar
    allow_credentials=True,
    allow_methods=["*"],            # permitir todos los métodos (GET, POST, etc.)
    allow_headers=["*"],            # permitir todos los headers
)



app.include_router(ideas.router, prefix=API_PREFIX)
app.include_router(ia.router, prefix="/api/v1")
