# Levanta a Qdrant por si solo con almacenamiento persistente
# Luego levanta FastAPI para conectarse a los otros servicios
sudo docker run -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant
