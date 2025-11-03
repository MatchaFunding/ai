from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer
from bertopic import BERTopic
import traceback

# Rutas de los controladores para cada servicio
from app.services.embeddings_factory import get_embeddings_provider
from app.services.qdrant_store import *
from app.api import ideas
from app.api import ia
from app.api import funds
from app.api import match
from app.api import projects
from app.api import premiumproject


from app.api.projects import subir_proyectos_del_backend
from app.api.projects import subir_proyectos_de_core
from app.api.funds import subir_instrumentos_de_core
from app.api.ideas import subir_ideas_del_backend

# Prefijo de la ruta para acceder a la API
API_PREFIX = "/api/v1"

# Carga los datos antes de habilitar el servicio
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicia el servicio de Qdrant y guarda sus propiedades
    print("Iniciando servicio de Qdrant...")
    provider = get_embeddings_provider()
    probe = await provider.embed(["_dim_probe"])
    vector_dim = len(probe[0])
    # Carga los datos en collecciones de Qdrant
    print("Cargando colecciones de Qdrant...")
    # Colección ideas: ideas de los usuarios vectorizadas
    ensure_collection("ideas", vector_dim)
    # Colección funds: fondos obtenidos del scrapping vectorizados
    ensure_collection("funds", vector_dim)
    # Tópicos de los fondos
    ensure_collection("funds_topics", NUMBER_OF_TOPICS)
    ensure_collection("similar_projects", vector_dim)
    ensure_collection("user_projects", vector_dim)
    # Inicia el modelo de BERTopic y guarda sus propiedades
    print("Iniciando modelo de BERTopic...")
    model = SentenceTransformer("jinaai/jina-embeddings-v2-base-es", trust_remote_code=True, device="cpu")
    topic_model = BERTopic.load("ayuda", embedding_model = model)
    # Guarda en memoria los servicios y modelos compartidos
    print("Estableciento estados...")
    app.state.provider = provider
    app.state.vector_dim = vector_dim
    app.state.topic_model = topic_model
    # Finalmente poblar con los datos en el BackEnd
    print("Cargando ideas de usuarios desde el BackEnd...")
    await subir_ideas_del_backend(provider)
    print("Cargando instrumentos desde el BackEnd...")
    await subir_instrumentos_de_core(provider, topic_model)
    print("Cargando proyectos desde el BackEnd...")
    await subir_proyectos_del_backend(provider)
    await subir_proyectos_de_core(provider)
    # Listo
    print("Modelos cargados exitosamente!")
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

# Middleware personalizado para manejar CORS en errores
@app.middleware("http")
async def cors_handler(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        print(f"Error en request {request.url}: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        # En caso de error, devolver respuesta con headers CORS
        response = JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error: {str(e)}"}
        )
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response

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
app.include_router(projects.router, prefix=API_PREFIX)
app.include_router(ideas.router, prefix=API_PREFIX)
app.include_router(funds.router, prefix=API_PREFIX)
app.include_router(match.router, prefix=API_PREFIX)
app.include_router(ia.router, prefix=API_PREFIX)
app.include_router(premiumproject.router, prefix=API_PREFIX)