export type RiskLevel = "Düşük" | "Orta" | "Yüksek" | "Kritik";

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
    deviation: "Akış yok",
    cause:
      "P-101A/B pompalarının ortak emiş hattında izolasyon vanasının kapalı kalması",
    consequence:
      "Reaktör beslemesinin kesilmesi; sıcaklık kontrolünün bozulması ve plansız duruş",
    safeguard:
      "Düşük akış alarmı FAL-101; yedek pompa otomatik devreye alma prosedürü",
    severity: 3,
    likelihood: 2,
    risk: "Orta",
    status: "İncelendi",
  },
  {
    id: 2,
    guideword: "Fazla",
    deviation: "Yüksek akış",
    cause: "Kontrol vanası FV-101'in tam açık konumda arızalanması",
    consequence:
      "Reaktörde besleme oranının artması; sıcaklık yükselmesi ve ürün spesifikasyon dışı üretim",
    safeguard:
      "Yüksek akış alarmı FAH-101; bağımsız yüksek sıcaklık tripi TSHH-204",
    severity: 4,
    likelihood: 2,
    risk: "Yüksek",
    status: "Taslak",
  },
  {
    id: 3,
    guideword: "Ters",
    deviation: "Ters akış",
    cause: "Pompa duruşunda çekvalfin sızdırması veya açık kalması",
    consequence:
      "Proses akışkanının depolama tankına geri dönmesi; tankta aşırı basınç ve kontaminasyon",
    safeguard: "Çekvalf bakım programı; pompa çıkışında motorlu izolasyon vanası",
    severity: 4,
    likelihood: 3,
    risk: "Kritik",
    status: "Eksik",
  },
  {
    id: 4,
    guideword: "Az",
    deviation: "Düşük akış",
    cause: "Emiş filtresinin kısmi tıkanması veya tank seviyesinin düşmesi",
    consequence: "Pompa kavitasyonu; mekanik hasar ve yanıcı akışkan kaçağı",
    safeguard: "Düşük tank seviye alarmı LAL-100; titreşim izleme",
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
    text: "Ortak emiş süzgecinin polimer birikimi nedeniyle tıkanması",
    confidence: "Yüksek",
    citations: [{
      chunk_id: "mock-s1",
      source_ref: "HAZOP-2024-018",
      section_ref: "Node 12 · P-204",
      excerpt: "Ortak emiş süzgecinde polimer birikimi gözlendi.",
    }],
    target: "cause",
  },
  {
    id: "s2",
    kind: "Önlem",
    text: "Pompa emiş ve basma basınç farkı için yüksek fark basınç alarmı",
    confidence: "Yüksek",
    citations: [{
      chunk_id: "mock-s2",
      source_ref: "HAZOP-2023-041",
      section_ref: "Node 07 · Santrifüj pompa",
      excerpt: "Fark basınç alarmı bağımsız izleme önlemi olarak kaydedildi.",
    }],
    target: "safeguard",
  },
  {
    id: "s3",
    kind: "Sonuç",
    text: "Kavitasyon kaynaklı mekanik salmastra hasarı ve yanıcı akışkan salımı",
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
  title: "Çalışma seçilmedi",
  client: "API bağlantısı yok",
  facility: "Veri yüklenemedi",
  progress: 0,
  reviewed_scenarios: 0,
  total_scenarios: 0,
};

export const nodes: WorkspaceNode[] = [
  {
    id: "node-t100",
    code: "N-01",
    name: "Hammadde tankı T-100",
    equipment_type: "Atmosferik tank",
    design_intent: "Hammaddeyi güvenli işletme sınırlarında depolamak.",
    scenario_count: 18,
    state: "complete",
  },
  {
    id: "node-p101",
    code: "N-02",
    name: "Besleme pompası P-101",
    equipment_type: "Santrifüj pompa",
    design_intent:
      "T-100 hammadde tankından R-201 reaktörüne kesintisiz ve kontrollü besleme sağlamak.",
    scenario_count: 24,
    state: "active",
  },
  {
    id: "node-e102",
    code: "N-03",
    name: "Isı eşanjörü E-102",
    equipment_type: "Kabuk-boru eşanjör",
    design_intent: "Besleme sıcaklığını reaksiyon giriş koşuluna getirmek.",
    scenario_count: 16,
    state: "review",
  },
  {
    id: "node-r201",
    code: "N-04",
    name: "Reaktör R-201",
    equipment_type: "Karıştırıcılı reaktör",
    design_intent: "Reaksiyonu tanımlı sıcaklık ve basınç aralığında yürütmek.",
    scenario_count: 31,
    state: "review",
  },
  {
    id: "node-v301",
    code: "N-05",
    name: "Ayırıcı V-301",
    equipment_type: "Basınçlı kap",
    design_intent: "Gaz ve sıvı fazlarını güvenli biçimde ayırmak.",
    scenario_count: 0,
    state: "empty",
  },
];

export const unavailableStatus: ProductStatus = {
  release: "MVP foundation",
  stage: "Ürün durumu yüklenemedi",
  overall_progress: 0,
  api_connected: false,
  persistence: "seed",
  ai_runtime: "contract_ready",
  deployment: "API bağlantısı bekleniyor",
  modules: [],
};
