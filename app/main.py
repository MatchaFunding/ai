from fastapi import FastAPI
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

# Rutas desactivadas para depurar
#from app.api import ideas, ia, funds, match, projects
#from app.services.embeddings_factory import get_embeddings_provider
#from app.services.qdrant_store import ensure_collection, COL_IDEAS, COL_FUNDS,COL_FUNDS_TOPICS,COL_PROYECT_SIMILARITY,NUMBER_OF_TOPICS

# Prefijo de la ruta para acceder a la API
API_PREFIX = "/api/v1"

# Carga los datos antes de habilitar el servicio
@asynccontextmanager
async def lifespan(app: FastAPI):
	## Obtiene el proveedor de los embeddings
    #provider = get_embeddings_provider()
	## Obtiene los detalles del proveedor
    #probe = await provider.embed(["_dim_probe"])
	## Almacena la dimension de los vectores
    #vector_dim = len(probe[0])
	## Carga los datos en collecciones de Qdrant
    #ensure_collection(COL_IDEAS, vector_dim)
    #ensure_collection(COL_FUNDS, vector_dim)
    #ensure_collection(COL_FUNDS_TOPICS, NUMBER_OF_TOPICS)
    #ensure_collection(COL_PROYECT_SIMILARITY, vector_dim)
    #ensure_collection("user_projects", vector_dim)
	## Guarda los datos en el estado de la aplicacion
    #app.state.provider = provider
    #app.state.vector_dim = vector_dim
    print(f"Cargando vectores y modelo de topicos...")
    yield

app = FastAPI(title="MatchaFunding - API de Inteligencia Artificial", version="0.1.0", lifespan=lifespan)

# Se habilita la API para CORS
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Para ver el estado de el servicio
@app.get("/")
def root():
    return {"message": "IA activa!"}

# Gestiona la salud de la API
@app.get(f"{API_PREFIX}/health")
def health():
    return {
        "status": "ok",
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "version": app.version,
        "service": app.title,
    }

# Routers para los diferentes servicios
#app.include_router(projects.router, prefix=API_PREFIX)
#app.include_router(ideas.router, prefix=API_PREFIX)
#app.include_router(funds.router, prefix=API_PREFIX)
#app.include_router(match.router, prefix=API_PREFIX)
#app.include_router(ia.router, prefix=API_PREFIX)
