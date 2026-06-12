export type RiskLevel = "Düşük" | "Orta" | "Yüksek" | "Kritik";

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
  confidence: "Yüksek" | "Orta";
  source: string;
  section: string;
  target: "cause" | "consequence" | "safeguard";
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
    source: "HAZOP-2024-018",
    section: "Node 12 · P-204",
    target: "cause",
  },
  {
    id: "s2",
    kind: "Önlem",
    text: "Pompa emiş ve basma basınç farkı için yüksek fark basınç alarmı",
    confidence: "Yüksek",
    source: "HAZOP-2023-041",
    section: "Node 07 · Santrifüj pompa",
    target: "safeguard",
  },
  {
    id: "s3",
    kind: "Sonuç",
    text: "Kavitasyon kaynaklı mekanik salmastra hasarı ve yanıcı akışkan salımı",
    confidence: "Orta",
    source: "IEC 61882",
    section: "§6.3.4 · Consequences",
    target: "consequence",
  },
];

export const nodes = [
  { code: "N-01", name: "Hammadde tankı T-100", count: 18, state: "complete" },
  { code: "N-02", name: "Besleme pompası P-101", count: 24, state: "active" },
  { code: "N-03", name: "Isı eşanjörü E-102", count: 16, state: "review" },
  { code: "N-04", name: "Reaktör R-201", count: 31, state: "review" },
  { code: "N-05", name: "Ayırıcı V-301", count: 0, state: "empty" },
];

