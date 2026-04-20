import os
from pathlib import Path
from typing import Dict, Any, List

from typing import List, Optional, Dict, Any, Sequence

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from sentence_transformers import SentenceTransformer
import numpy as np

from .embeddings import SentenceTransformerEmbeddings

class EmbeddingsFilter:
    def __init__(self, embeddings_model, similarity_threshold=0.7):
        self.embeddings_model = embeddings_model
        self.similarity_threshold = similarity_threshold

    async def acompress_documents(self, documents: List[Document], query: str) -> List[Document]:
        return self.compress_documents(documents, query)

    def compress_documents(self, documents: List[Document], query: str) -> List[Document]:
        if not documents:
            return []
        
        # Get embeddings for the query and documents
        query_embedding = self.embeddings_model.encode(query, convert_to_numpy=True, normalize_embeddings=True)
        doc_texts = [doc.page_content for doc in documents]
        doc_embeddings = self.embeddings_model.encode(doc_texts, convert_to_numpy=True, normalize_embeddings=True)
        
        # Calculate similarities and filter documents
        similarities = np.dot(doc_embeddings, query_embedding)
        filtered_docs = [doc for doc, sim in zip(documents, similarities) if sim > self.similarity_threshold]
        return filtered_docs


class RetrievalService:
    def __init__(self, storage_dir: Path) -> None:
        self.storage_dir = storage_dir
        self.index_dir = storage_dir / "faiss_index"
        model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        self.st_model = SentenceTransformer(model_name)
        self.embedder = SentenceTransformerEmbeddings(self.st_model)
        self._load_index()

        top_k = int(os.getenv("TOP_K", "6"))
        fetch_k = int(os.getenv("FETCH_K", "20"))
        lambda_mult = float(os.getenv("MMR_LAMBDA", "0.5"))
        self.top_k = top_k
        self.fetch_k = fetch_k
        self.lambda_mult = lambda_mult

        # Compression with embeddings similarity filter to remove redundancy
        self.compressor = EmbeddingsFilter(
            embeddings_model=self.st_model,
            similarity_threshold=0.3,
        )

    def _load_index(self) -> None:
        try:
            self.db = FAISS.load_local(
                str(self.index_dir),
                self.embedder,
                allow_dangerous_deserialization=True,
            )
        except Exception as e:
            print(f"Could not load index: {e}")
            self.db = None

    def _ensure_db(self) -> None:
        if self.db is None:
            print("Creating empty FAISS index as fallback...")
            self.db = FAISS.from_texts(
                texts=["dummy text"],
                embedding=self.embedder,
            )

    def _embed(self, text: str):
        return self.st_model.encode([text], convert_to_numpy=True, normalize_embeddings=True)[0]

    def _mmr_rerank(self, query_embedding, doc_embeddings, docs, k=4):
        """Rerank documents using Maximal Marginal Relevance."""
        if len(docs) <= k:
            return docs
        
        # Initialize
        selected = []
        remaining = list(range(len(docs)))
        
        # Select first document with highest similarity to query
        sims = [np.dot(query_embedding, doc_embeddings[i]) for i in remaining]
        first_idx = remaining[np.argmax(sims)]
        selected.append(first_idx)
        remaining.remove(first_idx)
        
        # Select remaining documents using MMR
        for _ in range(min(k-1, len(remaining))):
            scores = []
            for idx in remaining:
                # Similarity to query
                sim_query = np.dot(query_embedding, doc_embeddings[idx])
                
                # Maximum similarity to selected documents
                sim_selected = max([np.dot(doc_embeddings[idx], doc_embeddings[sel]) for sel in selected])
                
                # MMR score
                mmr_score = self.lambda_mult * sim_query - (1-self.lambda_mult) * sim_selected
                scores.append(mmr_score)
            
            next_idx = remaining[np.argmax(scores)]
            selected.append(next_idx)
            remaining.remove(next_idx)
        
        return [docs[i] for i in selected]

    def _mmr_search(self, query: str) -> List[Document]:
        # First, get documents using similarity search
        docs = self.db.similarity_search(
            query,
            k=self.fetch_k
        )
        
        # Get embeddings for MMR reranking
        query_embedding = self._embed(query)
        doc_texts = [doc.page_content for doc in docs]
        doc_embeddings = self.st_model.encode(doc_texts, convert_to_numpy=True, normalize_embeddings=True)
        
        # Apply MMR reranking
        reranked_docs = self._mmr_rerank(
            query_embedding,
            doc_embeddings,
            docs,
            k=self.top_k
        )
        
        # Apply compression filter
        filtered_docs = self.compressor.compress_documents(reranked_docs, query)
        return filtered_docs

    def retrieve_profile(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        self._ensure_db()
        profile_text = self._profile_to_text(profile)
        docs = self._mmr_search(profile_text)
        return {"query": profile_text, "documents": docs}

    def retrieve_query(self, question: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        self._ensure_db()
        q = question.strip()
        if profile:
            q = f"Question: {q}\nProfile: {self._profile_to_text(profile)}"
        docs = self._mmr_search(q)
        return {"query": q, "documents": docs}

    @staticmethod
    def _profile_to_text(profile: Dict[str, Any]) -> str:
        branch = profile.get("branch") or ""
        interests = ", ".join(profile.get("interests") or [])
        skills = ", ".join(profile.get("skills") or [])
        goal = profile.get("goal") or ""
        return (
            f"Branch: {branch}\n"
            f"Interests: {interests}\n"
            f"Skills: {skills}\n"
            f"Goal: {goal}"
        )


