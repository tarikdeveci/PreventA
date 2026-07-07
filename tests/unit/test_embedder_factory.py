"""The embedder factory must default to the keyless in-process backend."""

from __future__ import annotations

from preventa.api.dependencies import get_embedder
from preventa.core.config import Settings
from preventa.features.rag.providers import HashingEmbedder, OllamaClient


def test_defaults_to_keyless_hashing_embedder() -> None:
    embedder = get_embedder(Settings(rag_embedder="hashing"))
    assert isinstance(embedder, HashingEmbedder)


def test_uses_ollama_when_configured() -> None:
    embedder = get_embedder(Settings(rag_embedder="ollama"))
    assert isinstance(embedder, OllamaClient)
