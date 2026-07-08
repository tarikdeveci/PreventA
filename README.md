# PreventA

PreventA is an on-prem process-safety platform for HAZOP, LOPA, and SIL workflows.
Its first AI feature is a grounded HAZOP deviation assistant that drafts causes,
consequences, and safeguards from past studies and controlled safety references.

The model does not make safety decisions. Suggestions require source citations and
remain pending until a qualified engineer accepts, edits, or rejects them.

## Stack

- React 19, TypeScript, and Vite
- Product UI designed around a keyboard-efficient HAZOP worksheet
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
Set-Location frontend
pnpm install
pnpm run dev
```

OpenAPI is available at `http://localhost:8000/docs`.
The React workspace is available at `http://localhost:5173`.

To run the complete containerized stack:

```powershell
docker compose up --build
```

The frontend container proxies `/api` requests to FastAPI.

## Product UI

The initial UI includes:

- study and node navigation,
- an editable HAZOP worksheet organised as a Cause → Consequence hierarchy
  (a cause spans its consequence rows, with an "add consequence" action),
- three-state risk per consequence — before safeguards, current, and after
  recommendations,
- source-cited AI suggestions that can be added to the selected draft row,
- LOPA and IPL assessment,
- a configurable risk matrix view,
- controlled-source inventory,
- responsive navigation and evidence drawers.

Product and visual decisions are recorded in `PRODUCT.md` and `DESIGN.md`.

## OpenPHA interoperability

PreventA reads and writes the OpenPHA `.opha` study format, so real client studies
can be loaded and an edited study exported back as a client-ready deliverable.

- Import flattens a study one row per consequence into the live worksheet
  (`POST /api/v1/studies/import`, raw `.opha` bytes as the body).
- The structured path maps the full OpenPHA tree (Study → Node → Deviation →
  Cause → Consequence, plus Safeguards, LOPA layers, Recommendations, the risk
  matrix and supporting registers) onto the ORM.
- `orm_to_opha` rebuilds a faithful `.opha` document from the database — the
  reverse export, proven by an `import → database → export → compare` round-trip.
- Severity/likelihood codes are resolved into ordinals via the study's risk
  matrix; the LOPA arithmetic is recomputed and checked against the target on
  import; the file's `Ds_Rev` revision is recorded and validated.

See `docs/architecture.md` (OpenPHA interoperability) for the module map.

## Deployment

Production runs on Vercel (frontend + serverless API, same-origin) at
`prevent-a.vercel.app`. Deploys are made with the Vercel CLI (`vercel --prod`);
the flat store adds new columns idempotently on cold start, so no manual
migration step is needed for it.

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
Set-Location frontend
pnpm run lint
pnpm run build
```
