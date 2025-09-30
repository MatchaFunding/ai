import os
from typing import Sequence, List
from sentence_transformers import SentenceTransformer
import anyio
from app.services.embeddings_base import EmbeddingsProvider

# Transforma un String a Booleano equivalente
def _str2bool(s: str | None, default: bool) -> bool:
    if s is None:
        return default
    return s.lower() in {"1", "true", "yes", "y", "on"}

# Clase que gestiona los embeddings de SBert
class SBertEmbeddings(EmbeddingsProvider):
    _model: SentenceTransformer | None = None

	# Constructor de la clase
    def __init__(self):
        self.model_name = os.getenv("EMBEDDINGS_MODEL", "intfloat/multilingual-e5-base")
        self.device = os.getenv("EMBEDDINGS_DEVICE", "cpu")
        self.normalize = _str2bool(os.getenv("EMBEDDINGS_NORMALIZE", "true"), True)
        self.local_only = _str2bool(os.getenv("HF_LOCAL_ONLY", "false"), False)
		
	# Establece el modelo a utilizar
    def _ensure_model(self) -> SentenceTransformer:
        if SBertEmbeddings._model is None:
            SBertEmbeddings._model = SentenceTransformer(
                self.model_name,
                device=self.device,
                cache_folder=os.getenv("TRANSFORMERS_CACHE", None),
                local_files_only=self.local_only,
            )
        return SBertEmbeddings._model
	
	# Funcion para embeddir textos hacia SBert
	# Es asincrona y utiliza un thread pool
    async def embed(self, texts: Sequence[str]) -> List[List[float]]:
        model = self._ensure_model()
        def _encode() -> List[List[float]]:
            emb = model.encode(
                list(texts),
                normalize_embeddings=self.normalize,
                convert_to_numpy=True,
                batch_size=int(os.getenv("EMBEDDINGS_BATCH_SIZE", "32")),
                show_progress_bar=False,
            )
            return emb.tolist()
        return await anyio.to_thread.run_sync(_encode)
