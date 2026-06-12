# PreventA Knowledge Graph

This is the navigation entrypoint for the PreventA code graph.

## Architecture map

- Application entry: `src/preventa/main.py`
- API wiring: `src/preventa/api/router.py`
- Deviation endpoint: `src/preventa/api/routes/rag.py`
- RAG orchestration: `src/preventa/features/rag/service.py`
- Hybrid retrieval: `src/preventa/features/rag/repository.py`
- Reciprocal rank fusion: `src/preventa/features/rag/fusion.py`
- Citation enforcement: `src/preventa/features/rag/guardrails.py`
- Ollama and reranker ports: `src/preventa/features/rag/providers.py`
- HAZOP persistence: `src/preventa/db/models/hazop.py`
- Corpus and audit persistence: `src/preventa/db/models/rag.py`

## Generated graph

- [Graph report](../GRAPH_REPORT.md)
- [Interactive graph](../graph.html)
- [Graph JSON](../graph.json)

The current deterministic graph contains 164 nodes, 412 edges, and 24 communities.
Documentation semantic extraction is pending because the local Ollama service was not
running during generation. Code relationships and README structure are indexed.

## Verified traversal

The architecture query connected `PreventA`, `Citation`, `Candidate`,
`DeviationAssistRequest`, `GeneratedDraft`, `require_citations()`, and the guardrail
tests. The graph records extracted schema containment and inferred test call edges.

