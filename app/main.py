from fastapi import FastAPI
from datetime import datetime, timezone
from contextlib import asynccontextmanager


from app.api import ideas, ia, funds, match,projects
from app.services.embeddings_factory import get_embeddings_provider
from app.services.qdrant_store import ensure_collection, COL_IDEAS, COL_FUNDS,COL_FUNDS_TOPICS,COL_PROYECT_SIMILARITY,NUMBER_OF_TOPICS
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    provider = get_embeddings_provider()
    
    probe = await provider.embed(["_dim_probe"])
    vector_dim = len(probe[0])

    ensure_collection(COL_IDEAS, vector_dim)
    ensure_collection(COL_FUNDS, vector_dim)
    ensure_collection(COL_FUNDS_TOPICS, NUMBER_OF_TOPICS)
    ensure_collection(COL_PROYECT_SIMILARITY, vector_dim)


    #
    app.state.provider = provider
    app.state.vector_dim = vector_dim

    yield

app = FastAPI(title="IA Service", version="0.1.0", lifespan=lifespan)
API_PREFIX = "/api/v1"

origins = [
    "http://localhost:5173",  # tu frontend local
    "http://127.0.0.1:5173",
    
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # qué orígenes aceptar
    allow_credentials=True,
    allow_methods=["*"],            # permitir todos los métodos (GET, POST, etc.)
    allow_headers=["*"],            # permitir todos los headers
)



@app.get(f"{API_PREFIX}/health")
def health():
    return {
        "status": "ok",
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "version": app.version,
        "service": app.title,
    }

# Routers
app.include_router(ideas.router, prefix=API_PREFIX)
app.include_router(ia.router,    prefix=API_PREFIX)
app.include_router(funds.router, prefix=API_PREFIX)
app.include_router(match.router, prefix=API_PREFIX)
app.include_router(projects.router, prefix=API_PREFIX)


from fastapi import FastAPI
from datetime import datetime, timezone

from app.api import ideas, ia, funds, match






