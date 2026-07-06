import hashlib
import math
import re
from typing import Any, Protocol

import httpx

from preventa.features.rag.prompts import SYSTEM_PROMPT
from preventa.features.rag.schemas import (
    DeviationAssistRequest,
    GeneratedDraft,
    RetrievedChunk,
)


class Embedder(Protocol):
    async def embed(self, text: str) -> list[float]: ...


class DraftGenerator(Protocol):
    @property
    def model_name(self) -> str: ...

    async def generate(
        self,
        request: DeviationAssistRequest,
        context: list[RetrievedChunk],
    ) -> GeneratedDraft: ...


class Reranker(Protocol):
    async def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        *,
        limit: int,
    ) -> list[RetrievedChunk]: ...


class HashingEmbedder(Embedder):
    """Deterministic, dependency-free embedder using signed feature hashing.

    It is NOT a semantic model — it captures lexical overlap (token unigrams and
    bigrams hashed into a fixed vector) so the hybrid retrieval pipeline can be
    exercised, tested and demoed against real pgvector without a model host or
    API key. Swap for a hosted embedding provider in production; the interface
    (``Embedder``) is identical, so nothing else changes.
    """

    def __init__(self, dimensions: int = 768) -> None:
        self._dimensions = dimensions

    async def embed(self, text: str) -> list[float]:
        vector = [0.0] * self._dimensions
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        grams = [*tokens, *(f"{a}_{b}" for a, b in zip(tokens, tokens[1:], strict=False))]
        for token in grams:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            value = int.from_bytes(digest, "big")
            bucket = value % self._dimensions
            sign = 1.0 if (value >> 63) & 1 else -1.0
            vector[bucket] += sign
        norm = math.sqrt(sum(component * component for component in vector))
        if norm > 0.0:
            vector = [component / norm for component in vector]
        return vector


class PassthroughReranker(Reranker):
    async def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        *,
        limit: int,
    ) -> list[RetrievedChunk]:
        del query
        return chunks[:limit]


class OllamaClient(Embedder, DraftGenerator):
    def __init__(
        self,
        *,
        base_url: str,
        chat_model: str,
        embed_model: str,
        timeout_seconds: float = 120.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._chat_model = chat_model
        self._embed_model = embed_model
        self._timeout = timeout_seconds

    @property
    def model_name(self) -> str:
        return self._chat_model

    async def embed(self, text: str) -> list[float]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/api/embed",
                json={"model": self._embed_model, "input": text},
            )
            response.raise_for_status()
            payload = response.json()
        return list(payload["embeddings"][0])

    async def generate(
        self,
        request: DeviationAssistRequest,
        context: list[RetrievedChunk],
    ) -> GeneratedDraft:
        user_payload: dict[str, Any] = {
            "task": request.model_dump(mode="json"),
            "context": [chunk.model_dump(mode="json") for chunk in context],
            "output_schema": GeneratedDraft.model_json_schema(),
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/api/chat",
                json={
                    "model": self._chat_model,
                    "stream": False,
                    "format": "json",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": str(user_payload)},
                    ],
                },
            )
            response.raise_for_status()
            payload = response.json()
        return GeneratedDraft.model_validate_json(payload["message"]["content"])
