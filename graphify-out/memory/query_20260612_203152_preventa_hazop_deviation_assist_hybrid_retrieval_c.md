---
type: "query"
date: "2026-06-12T20:31:52.875030+00:00"
question: "PreventA HAZOP deviation assist hybrid retrieval citation guardrail API database architecture"
contributor: "graphify"
source_nodes: ["PreventA", "Citation", "Candidate", "DeviationAssistRequest", "GeneratedDraft", "require_citations()"]
---

# Q: PreventA HAZOP deviation assist hybrid retrieval citation guardrail API database architecture

## Answer

PreventA is a modular FastAPI application where the deviation-assist API orchestrates hybrid PostgreSQL FTS and pgvector retrieval, RRF fusion, a reranker port, local Ollama generation, citation membership validation, and persisted retrieval traces. HAZOP study data and RAG audit data are separated into explicit model modules. Every displayed candidate requires a citation from the retrieved context.

## Source Nodes

- PreventA
- Citation
- Candidate
- DeviationAssistRequest
- GeneratedDraft
- require_citations()