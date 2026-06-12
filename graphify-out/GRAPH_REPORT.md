# Graph Report - PreventA  (2026-06-13)

## Corpus Check
- 63 files · ~12,292 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 398 nodes · 864 edges · 38 communities (25 shown, 13 thin omitted)
- Extraction: 54% EXTRACTED · 46% INFERRED · 0% AMBIGUOUS · INFERRED: 395 edges (avg confidence: 0.54)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `fccfe9b0`
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
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 37|Community 37]]

## God Nodes (most connected - your core abstractions)
1. `DeviationAssistRequest` - 31 edges
2. `RetrievedChunk` - 28 edges
3. `GeneratedDraft` - 26 edges
4. `WorkspaceRepository` - 24 edges
5. `StudyCreate` - 22 edges
6. `HybridRetrievalRepository` - 21 edges
7. `NodeCreate` - 21 edges
8. `RowCreate` - 21 edges
9. `RowUpdate` - 21 edges
10. `LopaLayerCreate` - 21 edges

## Surprising Connections (you probably didn't know these)
- `test_rrf_is_deterministic_for_tied_scores()` --calls--> `reciprocal_rank_fusion()`  [INFERRED]
  tests/unit/test_fusion.py → src/preventa/features/rag/fusion.py
- `test_rrf_rewards_items_returned_by_both_retrievers()` --calls--> `reciprocal_rank_fusion()`  [INFERRED]
  tests/unit/test_fusion.py → src/preventa/features/rag/fusion.py
- `test_rejects_empty_generation()` --calls--> `require_citations()`  [INFERRED]
  tests/unit/test_guardrails.py → src/preventa/features/rag/guardrails.py
- `test_workspace_exposes_api_seed_transparently()` --calls--> `get_workspace()`  [INFERRED]
  tests/unit/test_workspace.py → src/preventa/features/workspace/service.py
- `test_accepts_candidate_with_source_citation()` --calls--> `require_citations()`  [INFERRED]
  tests/unit/test_guardrails.py → src/preventa/features/rag/guardrails.py

## Import Cycles
- 1-file cycle: `src/preventa/main.py -> src/preventa/main.py`
- 1-file cycle: `src/preventa/features/rag/guardrails.py -> src/preventa/features/rag/guardrails.py`

## Communities (38 total, 13 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.14
Nodes (41): get_deviation_assist_service(), BaseSettings, Settings, DeviationAssistService, DeviationAssistServiceDep, DraftGenerator, Embedder, Protocol (+33 more)

### Community 1 - "Community 1"
Cohesion: 0.16
Nodes (25): Collection, Base, TimestampMixin, UUIDPrimaryKeyMixin, DeclarativeBase, HazopNode, HazopWorksheetRow, ReviewStatus (+17 more)

### Community 2 - "Community 2"
Cohesion: 0.18
Nodes (34): Response, add_lopa_layer(), create_node(), create_row(), create_study(), delete_row(), download_report(), list_rows() (+26 more)

### Community 3 - "Community 3"
Cohesion: 0.20
Nodes (8): ItemId, KnowledgeChunk, Fuse ordered result lists while retaining candidates unique to one retriever., reciprocal_rank_fusion(), Select, RetrievedChunk, test_rrf_is_deterministic_for_tied_scores(), test_rrf_rewards_items_returned_by_both_retrievers()

### Community 4 - "Community 4"
Cohesion: 0.20
Nodes (5): get_settings(), configure_logging(), FastAPI, create_app(), lifespan()

### Community 5 - "Community 5"
Cohesion: 0.15
Nodes (16): BaseModel, product_status(), workspace(), ProductStatusResponse, WorkspaceResponse, test_product_status_reports_unfinished_persistence(), test_workspace_exposes_api_seed_transparently(), DeliveryModule (+8 more)

### Community 6 - "Community 6"
Cohesion: 0.42
Nodes (7): citation_accuracy(), evaluate(), main(), Any, recall_at_k(), test_citation_accuracy(), test_recall_at_k()

### Community 7 - "Community 7"
Cohesion: 0.33
Nodes (5): Module boundaries, Planned extensions, PreventA Architecture, Retrieval lifecycle, Safety invariants

### Community 8 - "Community 8"
Cohesion: 0.29
Nodes (6): Current API, PreventA, Product UI, Run locally, Stack, Verification

### Community 11 - "Community 11"
Cohesion: 0.08
Nodes (25): dependencies, lucide-react, react, react-dom, devDependencies, eslint, @eslint/js, eslint-plugin-react-hooks (+17 more)

### Community 24 - "Community 24"
Cohesion: 0.07
Nodes (30): createHazopRow(), createNode(), createStudy(), deleteHazopRow(), fetchNodes(), fetchProductStatus(), fetchRows(), fetchStudies() (+22 more)

### Community 25 - "Community 25"
Cohesion: 0.11
Nodes (17): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+9 more)

### Community 26 - "Community 26"
Cohesion: 0.17
Nodes (11): compilerOptions, allowImportingTsExtensions, lib, module, moduleDetection, moduleResolution, noEmit, skipLibCheck (+3 more)

### Community 27 - "Community 27"
Cohesion: 0.22
Nodes (8): Accessibility & Inclusion, Anti-references, Brand Personality, Design Principles, Product, Product Purpose, Register, Users

### Community 28 - "Community 28"
Cohesion: 0.25
Nodes (7): Color, Components, Design System, Direction, Layout, Motion, Typography

### Community 29 - "Community 29"
Cohesion: 0.50
Nodes (3): Answer, Q: PreventA HAZOP deviation assist hybrid retrieval citation guardrail API database architecture, Source Nodes

### Community 37 - "Community 37"
Cohesion: 0.16
Nodes (14): Row, Any, Any, Path, test_workspace_crud_and_lopa(), WorkspaceRepository, audit(), connection() (+6 more)

## Knowledge Gaps
- **91 isolated node(s):** `name`, `private`, `version`, `type`, `dev` (+86 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `GeneratedDraft` connect `Community 0` to `Community 1`, `Community 5`?**
  _High betweenness centrality (0.065) - this node is a cross-community bridge._
- **Why does `UUID` connect `Community 1` to `Community 0`, `Community 37`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Why does `DeviationAssistRequest` connect `Community 0` to `Community 3`, `Community 5`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Are the 29 inferred relationships involving `DeviationAssistRequest` (e.g. with `DeviationAssistServiceDep` and `DraftGenerator`) actually correct?**
  _`DeviationAssistRequest` has 29 INFERRED edges - model-reasoned connections that need verification._
- **Are the 26 inferred relationships involving `RetrievedChunk` (e.g. with `DraftGenerator` and `Embedder`) actually correct?**
  _`RetrievedChunk` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Are the 24 inferred relationships involving `GeneratedDraft` (e.g. with `Collection` and `DraftGenerator`) actually correct?**
  _`GeneratedDraft` has 24 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `WorkspaceRepository` (e.g. with `test_workspace_crud_and_lopa()` and `LopaLayerCreate`) actually correct?**
  _`WorkspaceRepository` has 7 INFERRED edges - model-reasoned connections that need verification._