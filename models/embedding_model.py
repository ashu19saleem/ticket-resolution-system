"""
Embedding model wrapper.

Wrapped behind a class (not used inline everywhere) so the rest of the
codebase doesn't care whether embeddings come from sentence-transformers,
OpenAI, or anything else later.
"""

from functools import lru_cache
from typing import List

from sentence_transformers import SentenceTransformer

from app.config import EMBEDDING_MODEL_NAME


class EmbeddingModel:
    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        self.model_name = model_name
        self._model = SentenceTransformer(model_name)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of texts. Returns list of float vectors."""
        if not texts:
            return []
        embeddings = self._model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True,  # cosine similarity becomes a dot product
        )
        return embeddings.tolist()

    def embed_query(self, query: str) -> List[float]:
        """Embed a single query string."""
        return self.embed_texts([query])[0]


@lru_cache(maxsize=1)
def get_embedding_model() -> EmbeddingModel:
    """
    Cached singleton so the (relatively heavy) model is loaded once per
    process, not once per request.
    """
    return EmbeddingModel()
