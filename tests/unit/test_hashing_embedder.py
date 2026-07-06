"""The dependency-free HashingEmbedder must be well-formed and deterministic."""

from __future__ import annotations

import math

from preventa.db.models.rag import EMBEDDING_DIMENSIONS
from preventa.features.rag.providers import HashingEmbedder


async def test_embedding_has_the_model_dimension() -> None:
    vector = await HashingEmbedder().embed("centrifugal pump no flow")
    assert len(vector) == EMBEDDING_DIMENSIONS


async def test_embedding_is_deterministic() -> None:
    embedder = HashingEmbedder()
    assert await embedder.embed("high pressure") == await embedder.embed("high pressure")


async def test_embedding_is_unit_normalised() -> None:
    vector = await HashingEmbedder().embed("reactor runaway high temperature")
    assert math.isclose(math.sqrt(sum(v * v for v in vector)), 1.0, abs_tol=1e-9)


async def test_empty_text_yields_zero_vector() -> None:
    vector = await HashingEmbedder().embed("")
    assert vector == [0.0] * EMBEDDING_DIMENSIONS
