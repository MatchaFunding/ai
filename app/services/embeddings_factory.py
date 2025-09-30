import os
from app.services.embeddings_base import EmbeddingsProvider
from app.services.providers.sbert_embeddings import SBertEmbeddings

# Carga el proveedor de los embeddings
def get_embeddings_provider() -> EmbeddingsProvider:
    provider = os.getenv("EMBEDDINGS_PROVIDER", "sbert").lower()
    if provider == "sbert":
        return SBertEmbeddings()
    raise ValueError(f"Proveedor no soportado: {provider}")
