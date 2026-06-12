# PreventA

PreventA is an on-prem process-safety platform for HAZOP, LOPA, and SIL workflows.
Its first AI feature is a grounded HAZOP deviation assistant that drafts causes,
consequences, and safeguards from past studies and controlled safety references.

The model does not make safety decisions. Suggestions require source citations and
remain pending until a qualified engineer accepts, edits, or rejects them.

## Stack

- FastAPI and Pydantic
- SQLAlchemy 2 async and Alembic
- PostgreSQL full-text search and pgvector
- Reciprocal rank fusion with a cross-encoder reranker port
- Local Ollama embeddings and generation

## Run locally

```powershell
Copy-Item .env.example .env
docker compose up -d postgres ollama
docker compose exec ollama ollama pull qwen2.5:7b
docker compose exec ollama ollama pull nomic-embed-text
python -m pip install -e ".[dev]"
alembic upgrade head
uvicorn preventa.main:app --reload
```

OpenAPI is available at `http://localhost:8000/docs`.

## Current API

`POST /api/v1/rag/deviation-assist` runs:

1. dense and sparse retrieval,
2. reciprocal rank fusion,
3. optional reranking,
4. local structured generation,
5. citation validation,
6. immutable retrieval and suggestion tracing.

See `docs/architecture.md` for boundaries and safety invariants, and
`docs/evaluation.md` for the held-out study evaluation plan.

## Verification

```powershell
ruff check .
pytest
python -m compileall src scripts
```

