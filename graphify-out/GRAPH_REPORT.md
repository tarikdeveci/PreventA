# Graph Report - .  (2026-06-13)

## Corpus Check
- Corpus is ~12,405 words - fits in a single context window. You may not need a graph.

## Summary
- 513 nodes · 1154 edges · 43 communities (26 shown, 17 thin omitted)
- Extraction: 57% EXTRACTED · 43% INFERRED · 0% AMBIGUOUS · INFERRED: 493 edges (avg confidence: 0.57)
- Token cost: 24,200 input · 6,200 output

## Community Hubs (Navigation)
- [[_COMMUNITY_RAG Deviation Assist Service|RAG Deviation Assist Service]]
- [[_COMMUNITY_Frontend API Client & HAZOP|Frontend API Client & HAZOP]]
- [[_COMMUNITY_Workspace API Routes|Workspace API Routes]]
- [[_COMMUNITY_React UI Components|React UI Components]]
- [[_COMMUNITY_SQLAlchemy DB Models|SQLAlchemy DB Models]]
- [[_COMMUNITY_CRUD Schemas & Safety Rules|CRUD Schemas & Safety Rules]]
- [[_COMMUNITY_Core Infrastructure|Core Infrastructure]]
- [[_COMMUNITY_DB Base & Mixins|DB Base & Mixins]]
- [[_COMMUNITY_Frontend Dependencies|Frontend Dependencies]]
- [[_COMMUNITY_TypeScript App Config|TypeScript App Config]]
- [[_COMMUNITY_Workspace Schemas & Tests|Workspace Schemas & Tests]]
- [[_COMMUNITY_Architecture & Deployment Docs|Architecture & Deployment Docs]]
- [[_COMMUNITY_FastAPI Entry & Router|FastAPI Entry & Router]]
- [[_COMMUNITY_TypeScript Node Config|TypeScript Node Config]]
- [[_COMMUNITY_Retrieval Evaluation|Retrieval Evaluation]]
- [[_COMMUNITY_Reciprocal Rank Fusion|Reciprocal Rank Fusion]]
- [[_COMMUNITY_DOCX Report Builder|DOCX Report Builder]]
- [[_COMMUNITY_Impeccable Live Config|Impeccable Live Config]]
- [[_COMMUNITY_Async DB Session|Async DB Session]]
- [[_COMMUNITY_TypeScript Root Config|TypeScript Root Config]]
- [[_COMMUNITY_Vercel Backend Config|Vercel Backend Config]]
- [[_COMMUNITY_App Package Init|App Package Init]]
- [[_COMMUNITY_DB Package Init|DB Package Init]]
- [[_COMMUNITY_Features Package Init|Features Package Init]]
- [[_COMMUNITY_Frontend Vercel Rewrites|Frontend Vercel Rewrites]]
- [[_COMMUNITY_Vercel Deployment Configs|Vercel Deployment Configs]]
- [[_COMMUNITY_PreventA Root Package|PreventA Root Package]]
- [[_COMMUNITY_RAG Package Init|RAG Package Init]]
- [[_COMMUNITY_API Routes Package Init|API Routes Package Init]]
- [[_COMMUNITY_Scripts Package Init|Scripts Package Init]]
- [[_COMMUNITY_Workspace Read Models Init|Workspace Read Models Init]]
- [[_COMMUNITY_AppRail Navigation|AppRail Navigation]]
- [[_COMMUNITY_Logging Configuration|Logging Configuration]]
- [[_COMMUNITY_Frontend Package Manifest|Frontend Package Manifest]]
- [[_COMMUNITY_Workspace API Router|Workspace API Router]]

## God Nodes (most connected - your core abstractions)
1. `DeviationAssistRequest` - 37 edges
2. `RetrievedChunk` - 34 edges
3. `GeneratedDraft` - 30 edges
4. `StudyCreate` - 28 edges
5. `NodeCreate` - 27 edges
6. `RowCreate` - 27 edges
7. `RowUpdate` - 27 edges
8. `LopaLayerCreate` - 27 edges
9. `NodeUpdate` - 26 edges
10. `WorkspaceRepository` - 24 edges

## Surprising Connections (you probably didn't know these)
- `SQLite Volatile Persistence` --semantically_similar_to--> `PostgreSQL + pgvector Service (compose)`  [AMBIGUOUS] [semantically similar]
  src/preventa/features/workspace/store.py → compose.yaml
- `Modular Monolith Architecture Pattern` --references--> `WorkspaceRepository`  [INFERRED]
  docs/architecture.md → src/preventa/features/workspace/repository.py
- `HazopRow Type` --semantically_similar_to--> `hazop_worksheet_rows DB Table`  [INFERRED] [semantically similar]
  frontend/src/data.ts → migrations/versions/20260612_0001_initial.py
- `Suggestion Type` --semantically_similar_to--> `rag_suggestions DB Table`  [INFERRED] [semantically similar]
  frontend/src/data.ts → migrations/versions/20260612_0001_initial.py
- `WorkspaceStudy Type` --semantically_similar_to--> `studies DB Table`  [INFERRED] [semantically similar]
  frontend/src/data.ts → migrations/versions/20260612_0001_initial.py

## Import Cycles
- 1-file cycle: `src/preventa/main.py -> src/preventa/main.py`
- 1-file cycle: `src/preventa/features/rag/guardrails.py -> src/preventa/features/rag/guardrails.py`

## Communities (43 total, 17 thin omitted)

### Community 0 - "RAG Deviation Assist Service"
Cohesion: 0.12
Nodes (50): get_deviation_assist_service(), BaseSettings, Settings, DeviationAssistService, DeviationAssistServiceDep, DraftGenerator, Embedder, KnowledgeChunk (+42 more)

### Community 1 - "Frontend API Client & HAZOP"
Cohesion: 0.07
Nodes (30): createHazopRow(), createNode(), createStudy(), deleteHazopRow(), fetchNodes(), fetchProductStatus(), fetchRows(), fetchStudies() (+22 more)

### Community 2 - "Workspace API Routes"
Cohesion: 0.21
Nodes (42): bool, Response, add_lopa_layer(), create_node(), create_row(), create_study(), delete_row(), download_report() (+34 more)

### Community 3 - "React UI Components"
Cohesion: 0.08
Nodes (37): App (Main React Component), RiskBadge Component, StatusBadge Component, StudyNavigator Component, createHazopRow API Function, createNode API Function, createStudy API Function, deleteHazopRow API Function (+29 more)

### Community 4 - "SQLAlchemy DB Models"
Cohesion: 0.17
Nodes (18): Row, Any, int, str, Any, int, Path, str (+10 more)

### Community 5 - "CRUD Schemas & Safety Rules"
Cohesion: 0.08
Nodes (33): Retrieval Lifecycle (7 steps), Safety Invariants (6 rules), LopaLayerCreate, NodeCreate, NodeUpdate, RowCreate, RowUpdate, StudyCreate (+25 more)

### Community 6 - "Core Infrastructure"
Cohesion: 0.12
Nodes (33): Application Settings, get_settings Function, get_db_session Async Session Provider, SQLAlchemy Declarative Base, Timestamp Mixin, UUID Primary Key Mixin, Reciprocal Rank Fusion, UngroundedSuggestionError (+25 more)

### Community 7 - "DB Base & Mixins"
Cohesion: 0.15
Nodes (26): Collection, Base, TimestampMixin, UUIDPrimaryKeyMixin, DeclarativeBase, HazopNode, HazopWorksheetRow, ReviewStatus (+18 more)

### Community 8 - "Frontend Dependencies"
Cohesion: 0.08
Nodes (25): dependencies, lucide-react, react, react-dom, devDependencies, eslint, @eslint/js, eslint-plugin-react-hooks (+17 more)

### Community 9 - "TypeScript App Config"
Cohesion: 0.11
Nodes (17): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+9 more)

### Community 10 - "Workspace Schemas & Tests"
Cohesion: 0.18
Nodes (14): BaseModel, ProductStatusResponse, WorkspaceResponse, test_product_status_reports_unfinished_persistence(), test_workspace_exposes_api_seed_transparently(), DeliveryModule, ProductStatusResponse, WorkspaceNode (+6 more)

### Community 11 - "Architecture & Deployment Docs"
Cohesion: 0.18
Nodes (14): Modular Monolith Architecture Pattern, Docker Compose Stack, Ollama Service (compose), PostgreSQL + pgvector Service (compose), citation_accuracy Metric, Held-out Evaluation Plan, recall@k Metric, Frontend Entry Point (index.html) (+6 more)

### Community 12 - "FastAPI Entry & Router"
Cohesion: 0.20
Nodes (5): get_settings(), configure_logging(), FastAPI, create_app(), lifespan()

### Community 13 - "TypeScript Node Config"
Cohesion: 0.17
Nodes (11): compilerOptions, allowImportingTsExtensions, lib, module, moduleDetection, moduleResolution, noEmit, skipLibCheck (+3 more)

### Community 14 - "Retrieval Evaluation"
Cohesion: 0.35
Nodes (10): citation_accuracy(), evaluate(), main(), Any, float, int, str, recall_at_k() (+2 more)

### Community 15 - "Reciprocal Rank Fusion"
Cohesion: 0.25
Nodes (7): ItemId, Fuse ordered result lists while retaining candidates unique to one retriever., reciprocal_rank_fusion(), float, int, test_rrf_is_deterministic_for_tied_scores(), test_rrf_rewards_items_returned_by_both_retrievers()

### Community 16 - "DOCX Report Builder"
Cohesion: 0.40
Nodes (4): bytes, object, str, build_docx()

### Community 17 - "Impeccable Live Config"
Cohesion: 0.40
Nodes (4): commentSyntax, cspChecked, files, insertBefore

## Ambiguous Edges - Review These
- `KnowledgeChunk ORM Model` → `KnowledgeChunk ORM Model`  [AMBIGUOUS]
  src/preventa/db/models/rag.py · relation: semantically_similar_to
- `SQLite Volatile Persistence` → `PostgreSQL + pgvector Service (compose)`  [AMBIGUOUS]
  src/preventa/features/workspace/store.py · relation: semantically_similar_to

## Knowledge Gaps
- **114 isolated node(s):** `files`, `insertBefore`, `commentSyntax`, `cspChecked`, `name` (+109 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `KnowledgeChunk ORM Model` and `KnowledgeChunk ORM Model`?**
  _Edge tagged AMBIGUOUS (relation: semantically_similar_to) - confidence is low._
- **What is the exact relationship between `SQLite Volatile Persistence` and `PostgreSQL + pgvector Service (compose)`?**
  _Edge tagged AMBIGUOUS (relation: semantically_similar_to) - confidence is low._
- **Why does `GeneratedDraft` connect `RAG Deviation Assist Service` to `Workspace Schemas & Tests`, `DB Base & Mixins`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Why does `UUID` connect `DB Base & Mixins` to `RAG Deviation Assist Service`, `SQLAlchemy DB Models`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Why does `DeviationAssistRequest` connect `RAG Deviation Assist Service` to `Workspace Schemas & Tests`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Are the 35 inferred relationships involving `DeviationAssistRequest` (e.g. with `DeviationAssistServiceDep` and `DraftGenerator`) actually correct?**
  _`DeviationAssistRequest` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 32 inferred relationships involving `RetrievedChunk` (e.g. with `DraftGenerator` and `Embedder`) actually correct?**
  _`RetrievedChunk` has 32 INFERRED edges - model-reasoned connections that need verification._