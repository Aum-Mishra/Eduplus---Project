from typing import List

from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer


class SentenceTransformerEmbeddings(Embeddings):
    """LangChain-compatible embedding wrapper for sentence-transformers."""

    def __init__(self, model: SentenceTransformer) -> None:
        self.model = model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        vectors = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return vectors.tolist()

    def embed_query(self, text: str) -> List[float]:
        vector = self.model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
        return vector.tolist()
