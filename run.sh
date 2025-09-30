# Levanta a Qdrant por si solo con almacenamiento persistente
# Luego levanta FastAPI para conectarse a los otros servicios
docker run -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant & \
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
