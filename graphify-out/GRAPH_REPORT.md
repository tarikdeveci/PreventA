# Graph Report - PreventA  (2026-06-12)

## Corpus Check
- 35 files · ~3,721 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 164 nodes · 412 edges · 24 communities (14 shown, 10 thin omitted)
- Extraction: 44% EXTRACTED · 56% INFERRED · 0% AMBIGUOUS · INFERRED: 232 edges (avg confidence: 0.52)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d579d7ae`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]

## God Nodes (most connected - your core abstractions)
1. `DeviationAssistRequest` - 31 edges
2. `RetrievedChunk` - 28 edges
3. `GeneratedDraft` - 26 edges
4. `HybridRetrievalRepository` - 21 edges
5. `UngroundedSuggestionError` - 20 edges
6. `DraftGenerator` - 20 edges
7. `Embedder` - 19 edges
8. `Reranker` - 19 edges
9. `Settings` - 18 edges
10. `DeviationAssistService` - 18 edges

## Surprising Connections (you probably didn't know these)
- `test_rrf_is_deterministic_for_tied_scores()` --calls--> `reciprocal_rank_fusion()`  [INFERRED]
  tests/unit/test_fusion.py → src/preventa/features/rag/fusion.py
- `test_rrf_rewards_items_returned_by_both_retrievers()` --calls--> `reciprocal_rank_fusion()`  [INFERRED]
  tests/unit/test_fusion.py → src/preventa/features/rag/fusion.py
- `test_rejects_empty_generation()` --calls--> `require_citations()`  [INFERRED]
  tests/unit/test_guardrails.py → src/preventa/features/rag/guardrails.py
- `test_accepts_candidate_with_source_citation()` --calls--> `require_citations()`  [INFERRED]
  tests/unit/test_guardrails.py → src/preventa/features/rag/guardrails.py
- `test_rejects_citation_outside_retrieved_context()` --calls--> `require_citations()`  [INFERRED]
  tests/unit/test_guardrails.py → src/preventa/features/rag/guardrails.py

## Import Cycles
- 1-file cycle: `src/preventa/main.py -> src/preventa/main.py`
- 1-file cycle: `src/preventa/features/rag/guardrails.py -> src/preventa/features/rag/guardrails.py`

## Communities (24 total, 10 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.25
Nodes (31): BaseModel, BaseSettings, Settings, DeviationAssistServiceDep, DraftGenerator, Embedder, Protocol, UngroundedSuggestionError (+23 more)

### Community 1 - "Community 1"
Cohesion: 0.29
Nodes (17): Base, TimestampMixin, UUIDPrimaryKeyMixin, DeclarativeBase, HazopNode, HazopWorksheetRow, ReviewStatus, Study (+9 more)

### Community 2 - "Community 2"
Cohesion: 0.19
Nodes (9): get_deviation_assist_service(), DeviationAssistService, OllamaClient, PassthroughReranker, SessionDep, SettingsDep, DeviationAssistRequest, GeneratedDraft (+1 more)

### Community 3 - "Community 3"
Cohesion: 0.20
Nodes (8): ItemId, KnowledgeChunk, Fuse ordered result lists while retaining candidates unique to one retriever., reciprocal_rank_fusion(), Select, RetrievedChunk, test_rrf_is_deterministic_for_tied_scores(), test_rrf_rewards_items_returned_by_both_retrievers()

### Community 4 - "Community 4"
Cohesion: 0.22
Nodes (5): get_settings(), configure_logging(), FastAPI, create_app(), lifespan()

### Community 5 - "Community 5"
Cohesion: 0.27
Nodes (8): Collection, require_citations(), Candidate, Citation, GeneratedDraft, test_accepts_candidate_with_source_citation(), test_rejects_citation_outside_retrieved_context(), test_rejects_empty_generation()

### Community 6 - "Community 6"
Cohesion: 0.42
Nodes (7): Any, citation_accuracy(), evaluate(), main(), recall_at_k(), test_citation_accuracy(), test_recall_at_k()

### Community 7 - "Community 7"
Cohesion: 0.33
Nodes (5): Module boundaries, Planned extensions, PreventA Architecture, Retrieval lifecycle, Safety invariants

### Community 8 - "Community 8"
Cohesion: 0.33
Nodes (5): Current API, PreventA, Run locally, Stack, Verification

## Knowledge Gaps
- **12 isolated node(s):** `Any`, `AsyncSession`, `ItemId`, `Stack`, `Run locally` (+7 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `UUID` connect `Community 1` to `Community 0`, `Community 5`?**
  _High betweenness centrality (0.145) - this node is a cross-community bridge._
- **Why does `GeneratedDraft` connect `Community 0` to `Community 1`, `Community 2`, `Community 5`?**
  _High betweenness centrality (0.133) - this node is a cross-community bridge._
- **Why does `HybridRetrievalRepository` connect `Community 0` to `Community 3`, `Community 11`?**
  _High betweenness centrality (0.082) - this node is a cross-community bridge._
- **Are the 29 inferred relationships involving `DeviationAssistRequest` (e.g. with `DeviationAssistServiceDep` and `DraftGenerator`) actually correct?**
  _`DeviationAssistRequest` has 29 INFERRED edges - model-reasoned connections that need verification._
- **Are the 26 inferred relationships involving `RetrievedChunk` (e.g. with `DraftGenerator` and `Embedder`) actually correct?**
  _`RetrievedChunk` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Are the 24 inferred relationships involving `GeneratedDraft` (e.g. with `Collection` and `DraftGenerator`) actually correct?**
  _`GeneratedDraft` has 24 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `HybridRetrievalRepository` (e.g. with `DraftGenerator` and `Embedder`) actually correct?**
  _`HybridRetrievalRepository` has 15 INFERRED edges - model-reasoned connections that need verification._