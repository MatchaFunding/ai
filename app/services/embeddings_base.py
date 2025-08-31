from abc import ABC, abstractmethod
from typing import Sequence, List

class EmbeddingsProvider(ABC):
    @abstractmethod
    async def embed(self, texts: Sequence[str]) -> List[List[float]]:
        """Un embedding por texto, en el mismo orden."""
        raise NotImplementedError
