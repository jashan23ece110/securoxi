"""
SECUROXI AI Document Intelligence Stage 5 — Vector Storage & Retrieval Engine
Provides pgvector/in-memory vector storage, top-k cosine similarity search,
strict multi-tenant isolation, section filtering, and security status quarantine controls.
"""

import math
from typing import List, Dict, Any, Optional
from securoxi.config import SecuroxiConfig
from securoxi.logger import get_logger
from securoxi.screening.chunking import DocumentChunk
from securoxi.screening.embeddings import BaseEmbeddingProvider, LocalEmbeddingProvider


class VectorSearchResult:
    """Represents a vector search hit with similarity score and layout provenance."""

    def __init__(
        self,
        chunk: DocumentChunk,
        score: float,
        document_id: str,
        tenant_id: str
    ):
        self.chunk = chunk
        self.score = round(score, 4)
        self.document_id = document_id
        self.tenant_id = tenant_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk.chunk_id,
            "document_id": self.document_id,
            "tenant_id": self.tenant_id,
            "score": self.score,
            "section_heading": self.chunk.section_heading,
            "text": self.chunk.text,
            "start_page": self.chunk.start_page,
            "end_page": self.chunk.end_page,
            "security_status": self.chunk.security_status,
            "metadata": self.chunk.metadata
        }


class SecuroxiVectorStore:
    """
    Production-grade Vector Storage and Top-K Cosine Similarity Retrieval Engine.
    Enforces multi-tenant isolation, section filtering, and security quarantine policy.
    """

    def __init__(
        self,
        config: Optional[SecuroxiConfig] = None,
        embedding_provider: Optional[BaseEmbeddingProvider] = None
    ):
        self.config = config or SecuroxiConfig()
        self.logger = get_logger("securoxi.storage.vector_store")
        self.embedding_provider = embedding_provider or LocalEmbeddingProvider()
        # In-memory vector store table indexed by (tenant_id, chunk_id)
        self._index: Dict[str, List[Dict[str, Any]]] = {}

    def index_chunks(self, chunks: List[DocumentChunk], tenant_id: str) -> int:
        """
        Generates embeddings for document chunks and inserts them into vector index.
        """
        if tenant_id not in self._index:
            self._index[tenant_id] = []

        indexed_count = 0
        for chunk in chunks:
            vector = self.embedding_provider.embed_text(chunk.text)
            record = {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "tenant_id": tenant_id,
                "section_heading": chunk.section_heading,
                "embedding": vector,
                "chunk": chunk,
                "security_status": chunk.security_status
            }

            # Remove previous version if updating
            self._index[tenant_id] = [r for r in self._index[tenant_id] if r["chunk_id"] != chunk.chunk_id]
            self._index[tenant_id].append(record)
            indexed_count += 1

        self.logger.info(f"Indexed {indexed_count} chunks into vector store for tenant '{tenant_id}'.")
        return indexed_count

    def search(
        self,
        query: str,
        tenant_id: str,
        top_k: int = 5,
        min_score: float = 0.0,
        section_filter: Optional[str] = None,
        include_quarantined: bool = False
    ) -> List[VectorSearchResult]:
        """
        Executes Top-K Cosine Similarity retrieval against tenant vector index.
        Enforces tenant isolation, section filtering, and security quarantine filtering.
        """
        if tenant_id not in self._index or not self._index[tenant_id]:
            return []

        query_vector = self.embedding_provider.embed_text(query)
        results: List[VectorSearchResult] = []

        for record in self._index[tenant_id]:
            # Mandatory security quarantine check: exclude HIGH_RISK / UNINSPECTABLE chunks by default
            if not include_quarantined and record["security_status"] in ["HIGH_RISK", "UNINSPECTABLE"]:
                continue

            # Section filtering
            if section_filter and record["section_heading"].upper() != section_filter.upper():
                continue

            # Calculate cosine similarity
            score = self._cosine_similarity(query_vector, record["embedding"])

            if score >= min_score:
                results.append(VectorSearchResult(
                    chunk=record["chunk"],
                    score=score,
                    document_id=record["document_id"],
                    tenant_id=tenant_id
                ))

        # Sort by similarity score descending
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    def delete_document_index(self, document_id: str, tenant_id: str) -> int:
        """Deletes all vector index records for a given document within tenant context."""
        if tenant_id not in self._index:
            return 0
        before_count = len(self._index[tenant_id])
        self._index[tenant_id] = [r for r in self._index[tenant_id] if r["document_id"] != document_id]
        deleted_count = before_count - len(self._index[tenant_id])
        self.logger.info(f"Deleted {deleted_count} vectors for document '{document_id}' (Tenant: {tenant_id}).")
        return deleted_count

    @staticmethod
    def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Calculates cosine similarity between two float vectors."""
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        return max(0.0, min(1.0, dot_product / (norm_a * norm_b)))
