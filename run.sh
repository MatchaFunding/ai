# Levanta a Qdrant por si solo con almacenamiento persistente
# Luego levanta FastAPI para conectarse a los otros servicios
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
