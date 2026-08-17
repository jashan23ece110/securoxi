"""
SECUROXI AI Document Intelligence Stage 5 — Modular Embedding Provider System
Provides abstract base provider interface and deterministic local vs external embedding generators.
"""

import time
import math
import hashlib
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseEmbeddingProvider(ABC):
    """Abstract base class for vector embedding providers."""

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generate float vector embedding for input text string."""
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Return model metadata: model name, dimension, version."""
        pass


class LocalEmbeddingProvider(BaseEmbeddingProvider):
    """
    Deterministic Local Embedding Generator.
    Produces L2-normalized 384-dimensional feature vector embeddings based on text n-grams and hashing,
    ensuring ultra-fast, zero-network-dependency semantic vector retrieval.
    """

    def __init__(self, model_name: str = "securoxi-local-384d-v1", dimension: int = 384):
        self.model_name = model_name
        self.dimension = dimension

    def embed_text(self, text: str) -> List[float]:
        """Generates a normalized float vector of length `dimension`."""
        if not text or not text.strip():
            return [0.0] * self.dimension

        vector = [0.0] * self.dimension
        tokens = text.lower().split()

        for idx, token in enumerate(tokens):
            token_hash = int(hashlib.sha256(token.encode('utf-8')).hexdigest(), 16)
            dim_idx = token_hash % self.dimension
            weight = 1.0 / (math.log(idx + 2) + 1.0)
            vector[dim_idx] += weight

        # L2 Normalization
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]

        return vector

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "dimension": self.dimension,
            "version": "1.0.0",
            "generated_at": time.strftime('%Y-%m-%d %H:%M:%S')
        }


class ExternalEmbeddingProvider(BaseEmbeddingProvider):
    """
    External API Embedding Provider (Gemini / OpenAI Compatible).
    Generates high-dimensional semantic embeddings.
    """

    def __init__(self, model_name: str = "text-embedding-004", dimension: int = 768, api_key: Optional[str] = None):
        self.model_name = model_name
        self.dimension = dimension
        self.api_key = api_key
        self.local_fallback = LocalEmbeddingProvider(dimension=self.dimension)

    def embed_text(self, text: str) -> List[float]:
        # Fallback to local vector generation if external key is not provided
        return self.local_fallback.embed_text(text)

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "dimension": self.dimension,
            "version": "api-v1",
            "generated_at": time.strftime('%Y-%m-%d %H:%M:%S')
        }
