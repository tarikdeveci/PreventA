export type RiskLevel = "Düşük" | "Orta" | "Yüksek" | "Kritik";

export type UserRole = "admin" | "facilitator" | "viewer";

export type AuthUser = {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  permissions: string[];
};

export type SessionResponse = {
  user: AuthUser;
};

export type LopaLayer = {
  id: string;
  row_id: number;
  description: string;
  pfd: number;
  is_valid: boolean;
  note: string;
};

export type HazopRow = {
  id: number;
  guideword: string;
  deviation: string;
  cause: string;
  consequence: string;
  safeguard: string;
  severity: number;
  likelihood: number;
  risk: RiskLevel;
  status: "İncelendi" | "Taslak" | "Eksik";
};

export type Suggestion = {
  id: string;
  kind: "Neden" | "Sonuç" | "Önlem";
  text: string;
  confidence: "Yüksek" | "Orta" | "Düşük";
  citations: Citation[];
  target: "cause" | "consequence" | "safeguard";
};

export type Citation = {
  chunk_id: string;
  source_ref: string;
  section_ref: string | null;
  excerpt: string;
};

export type DeviationAssistRequest = {
  study_id: string;
  node_id: string;
  equipment_type: string;
  design_intent: string;
  parameter: string;
  guideword: string;
  deviation: string;
  existing_safeguards: string[];
};

export type DeviationAssistResponse = {
  suggestion_id: string;
  candidates: Array<{
    kind: "cause" | "consequence" | "safeguard";
    text: string;
    citations: Citation[];
    confidence: "low" | "medium" | "high";
  }>;
  disclaimer: string;
};

// Keyless retrieval-only evidence (POST /api/v1/rag/deviation-evidence):
// hybrid dense+sparse search returns cited source passages, no LLM generation.
export type RetrievedChunk = {
  chunk_id: string;
  document_id: string;
  source_ref: string;
  section_ref: string | null;
  content: string;
  dense_rank: number | null;
  sparse_rank: number | null;
  fused_score: number;
  rerank_score: number | null;
};

export type WorkspaceStudy = {
  id: string;
  title: string;
  client: string;
  facility: string;
  progress: number;
  reviewed_scenarios: number;
  total_scenarios: number;
};

export type StudyListItem = {
  id: string;
  title: string;
  client: string;
  facility: string;
  status: string;
  node_count: number;
};

export type LibraryEntry = {
  id: string;
  equipment_type: string;
  guideword: string;
  deviation: string;
  cause: string;
  consequence: string;
  safeguard: string;
  severity: number;
  likelihood: number;
  source_ref: string;
  risk: RiskLevel;
};

export type StudySource = {
  id: string;
  study_id: string;
  title: string;
  source_type: "Standard" | "Historical study" | "Procedure" | "Drawing" | "Other";
  reference: string;
  section_count: number;
  is_active: boolean;
  indexed_at: string;
};

export type RiskMatrixSettings = {
  study_id: string;
  low_max: number;
  medium_max: number;
  high_max: number;
  revision: number;
  updated_at: string;
};

export type AuditEntry = {
  id: number;
  entity_type: string;
  entity_id: string;
  action: string;
  detail: string;
  created_at: string;
};

export type ReportEntry = {
  id: string;
  study_id: string;
  node_id: string;
  filename: string;
  created_by: string;
  created_at: string;
  study_title: string;
  node_name: string;
};

export type WorkspaceNode = {
  id: string;
  code: string;
  name: string;
  equipment_type: string;
  design_intent: string;
  scenario_count: number;
  state: "complete" | "active" | "review" | "empty";
};

export type WorkspaceResponse = {
  source: "api_seed" | "database";
  study: WorkspaceStudy;
  active_node_id: string;
  nodes: WorkspaceNode[];
  rows: HazopRow[];
  suggestions: Suggestion[];
};

export type DeliveryModule = {
  id: string;
  name: string;
  status: "complete" | "in_progress" | "planned";
  progress: number;
  detail: string;
};

export type ProductStatus = {
  release: string;
  stage: string;
  overall_progress: number;
  api_connected: boolean;
  persistence: "seed" | "volatile_sqlite" | "postgresql";
  ai_runtime: "contract_ready" | "ollama_connected";
  deployment: string;
  modules: DeliveryModule[];
};

export const initialRows: HazopRow[] = [
  {
    id: 1,
    guideword: "Yok",
    deviation: "No flow",
    cause:
      "The isolation valve remains closed on the common suction header for pumps P-101A/B",
    consequence:
      "Loss of reactor feed, temperature control disruption and unplanned shutdown",
    safeguard:
      "Low-flow alarm FAL-101; automatic standby pump startup procedure",
    severity: 3,
    likelihood: 2,
    risk: "Orta",
    status: "İncelendi",
  },
  {
    id: 2,
    guideword: "Fazla",
    deviation: "High flow",
    cause: "Control valve FV-101 fails fully open",
    consequence:
      "Increased reactor feed rate, temperature rise and off-specification production",
    safeguard:
      "High-flow alarm FAH-101; independent high-temperature trip TSHH-204",
    severity: 4,
    likelihood: 2,
    risk: "Yüksek",
    status: "Taslak",
  },
  {
    id: 3,
    guideword: "Ters",
    deviation: "Reverse flow",
    cause: "Check valve leaks or remains open while the pump is stopped",
    consequence:
      "Process fluid returns to the storage tank, causing overpressure and contamination",
    safeguard: "Check valve maintenance program; motorized isolation valve at pump discharge",
    severity: 4,
    likelihood: 3,
    risk: "Kritik",
    status: "Eksik",
  },
  {
    id: 4,
    guideword: "Az",
    deviation: "Low flow",
    cause: "Partial suction strainer blockage or low tank level",
    consequence: "Pump cavitation, mechanical damage and flammable fluid release",
    safeguard: "Low tank level alarm LAL-100; vibration monitoring",
    severity: 3,
    likelihood: 3,
    risk: "Yüksek",
    status: "Taslak",
  },
];

export const suggestions: Suggestion[] = [
  {
    id: "s1",
    kind: "Neden",
    text: "Common suction strainer blockage caused by polymer buildup",
    confidence: "Yüksek",
    citations: [{
      chunk_id: "mock-s1",
      source_ref: "HAZOP-2024-018",
      section_ref: "Node 12 · P-204",
      excerpt: "Polymer buildup was observed in the common suction strainer.",
    }],
    target: "cause",
  },
  {
    id: "s2",
    kind: "Önlem",
    text: "High differential-pressure alarm across pump suction and discharge",
    confidence: "Yüksek",
    citations: [{
      chunk_id: "mock-s2",
      source_ref: "HAZOP-2023-041",
      section_ref: "Node 07 · Centrifugal pump",
      excerpt: "The differential-pressure alarm was recorded as an independent monitoring safeguard.",
    }],
    target: "safeguard",
  },
  {
    id: "s3",
    kind: "Sonuç",
    text: "Mechanical seal damage and flammable fluid release caused by cavitation",
    confidence: "Orta",
    citations: [{
      chunk_id: "mock-s3",
      source_ref: "IEC 61882",
      section_ref: "§6.3.4 · Consequences",
      excerpt: "Consequences should include credible equipment damage and loss of containment.",
    }],
    target: "consequence",
  },
];

export const emptyStudy: WorkspaceStudy = {
  id: "",
  title: "No study selected",
  client: "API unavailable",
  facility: "Data could not be loaded",
  progress: 0,
  reviewed_scenarios: 0,
  total_scenarios: 0,
};

export const nodes: WorkspaceNode[] = [
  {
    id: "node-t100",
    code: "N-01",
    name: "Feedstock Tank T-100",
    equipment_type: "Atmospheric tank",
    design_intent: "Store feedstock within safe operating limits.",
    scenario_count: 18,
    state: "complete",
  },
  {
    id: "node-p101",
    code: "N-02",
    name: "Feed Pump P-101",
    equipment_type: "Centrifugal pump",
    design_intent:
      "Provide continuous, controlled feed from feedstock tank T-100 to reactor R-201.",
    scenario_count: 24,
    state: "active",
  },
  {
    id: "node-e102",
    code: "N-03",
    name: "Heat Exchanger E-102",
    equipment_type: "Shell-and-tube heat exchanger",
    design_intent: "Bring the feed temperature to reactor inlet conditions.",
    scenario_count: 16,
    state: "review",
  },
  {
    id: "node-r201",
    code: "N-04",
    name: "Reactor R-201",
    equipment_type: "Agitated reactor",
    design_intent: "Maintain the reaction within its defined temperature and pressure envelope.",
    scenario_count: 31,
    state: "review",
  },
  {
    id: "node-v301",
    code: "N-05",
    name: "Separator V-301",
    equipment_type: "Pressure vessel",
    design_intent: "Safely separate the gas and liquid phases.",
    scenario_count: 0,
    state: "empty",
  },
];

export const unavailableStatus: ProductStatus = {
  release: "MVP foundation",
  stage: "Product status unavailable",
  overall_progress: 0,
  api_connected: false,
  persistence: "seed",
  ai_runtime: "contract_ready",
  deployment: "Waiting for API connection",
  modules: [],
};
