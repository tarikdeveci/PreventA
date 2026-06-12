import {
  Activity,
  AlertTriangle,
  Archive,
  BookOpen,
  Bot,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  CircleHelp,
  ClipboardCheck,
  Clock3,
  Download,
  FileClock,
  FileOutput,
  Files,
  Gauge,
  History,
  LayoutGrid,
  Menu,
  MoreHorizontal,
  PanelRightClose,
  Plus,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
  Table2,
  X,
} from "lucide-react";
import { useMemo, useState } from "react";
import { initialRows, nodes, suggestions, type HazopRow } from "./data";

type WorkspaceTab = "HAZOP" | "LOPA" | "Risk matrisi" | "Kaynaklar";

const workspaceTabs: { label: WorkspaceTab; count?: number }[] = [
  { label: "HAZOP", count: 24 },
  { label: "LOPA", count: 3 },
  { label: "Risk matrisi" },
  { label: "Kaynaklar", count: 12 },
];

function RiskBadge({ level }: { level: HazopRow["risk"] }) {
  return <span className={`risk-badge risk-${level.toLocaleLowerCase("tr")}`}>{level}</span>;
}

function StatusBadge({ status }: { status: HazopRow["status"] }) {
  const icon =
    status === "İncelendi" ? (
      <CheckCircle2 size={13} />
    ) : status === "Eksik" ? (
      <AlertTriangle size={13} />
    ) : (
      <Clock3 size={13} />
    );
  return (
    <span className={`status-badge status-${status.toLocaleLowerCase("tr")}`}>
      {icon}
      {status}
    </span>
  );
}

function AppRail() {
  return (
    <aside className="app-rail" aria-label="Ana uygulama">
      <button className="brand-mark" aria-label="PreventA ana sayfa">
        <ShieldCheck size={25} strokeWidth={2.2} />
      </button>
      <nav className="rail-nav" aria-label="Uygulama bölümleri">
        <button className="rail-button is-active" aria-label="Çalışmalar" title="Çalışmalar">
          <Files size={20} />
        </button>
        <button className="rail-button" aria-label="Senaryo kütüphanesi" title="Senaryo kütüphanesi">
          <BookOpen size={20} />
        </button>
        <button className="rail-button" aria-label="Raporlar" title="Raporlar">
          <FileOutput size={20} />
        </button>
        <button className="rail-button" aria-label="Denetim geçmişi" title="Denetim geçmişi">
          <History size={20} />
        </button>
      </nav>
      <div className="rail-footer">
        <button className="rail-button" aria-label="Yardım" title="Yardım">
          <CircleHelp size={20} />
        </button>
        <button className="rail-button" aria-label="Ayarlar" title="Ayarlar">
          <Settings size={20} />
        </button>
        <button className="avatar-button" aria-label="Tarık Deveci hesabı" title="Tarık Deveci">
          TD
        </button>
      </div>
    </aside>
  );
}

function StudyNavigator({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [query, setQuery] = useState("");
  const filteredNodes = nodes.filter((node) =>
    `${node.code} ${node.name}`.toLocaleLowerCase("tr").includes(query.toLocaleLowerCase("tr")),
  );

  return (
    <>
      {open && <button className="nav-scrim" onClick={onClose} aria-label="Navigasyonu kapat" />}
      <aside className={`study-nav ${open ? "is-open" : ""}`} aria-label="Çalışma navigasyonu">
        <div className="study-nav-header">
          <div>
            <span className="context-label">Aktif çalışma</span>
            <strong>Ünite 200 HAZOP</strong>
          </div>
          <button className="icon-button mobile-only" onClick={onClose} aria-label="Navigasyonu kapat">
            <X size={18} />
          </button>
        </div>

        <button className="study-switcher">
          <span className="study-monogram">RA</span>
          <span>
            <strong>Reaktör Alanı</strong>
            <small>ACWA Power · Konya</small>
          </span>
          <ChevronDown size={16} />
        </button>

        <div className="nav-section">
          <div className="nav-section-title">
            <span>Çalışma yapısı</span>
            <button className="compact-icon" aria-label="Yeni bölüm ekle">
              <Plus size={15} />
            </button>
          </div>
          <button className="nav-row">
            <LayoutGrid size={17} />
            <span>Genel bakış</span>
          </button>
          <button className="nav-row">
            <ClipboardCheck size={17} />
            <span>Çalışma bilgileri</span>
          </button>
          <button className="nav-row">
            <Gauge size={17} />
            <span>Risk matrisi</span>
            <span className="nav-meta">5 × 5</span>
          </button>
        </div>

        <div className="nav-section nodes-section">
          <div className="nav-section-title">
            <span>Node'lar</span>
            <span className="nav-count">5</span>
          </div>
          <label className="node-search">
            <Search size={15} aria-hidden="true" />
            <span className="sr-only">Node ara</span>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Node ara"
            />
          </label>
          <div className="node-list">
            {filteredNodes.map((node) => (
              <button
                className={`node-row ${node.state === "active" ? "is-active" : ""}`}
                key={node.code}
              >
                <span className={`node-state node-state-${node.state}`} aria-hidden="true" />
                <span className="node-copy">
                  <small>{node.code}</small>
                  <strong>{node.name}</strong>
                </span>
                <span className="node-count">{node.count}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="study-nav-footer">
          <div className="progress-copy">
            <span>Çalışma ilerlemesi</span>
            <strong>%62</strong>
          </div>
          <div className="progress-track" aria-label="Çalışma ilerlemesi yüzde 62">
            <span style={{ width: "62%" }} />
          </div>
          <small>89 / 143 senaryo incelendi</small>
        </div>
      </aside>
    </>
  );
}

function TopBar({
  onOpenNav,
  onExport,
}: {
  onOpenNav: () => void;
  onExport: () => void;
}) {
  return (
    <header className="top-bar">
      <div className="top-context">
        <button className="icon-button nav-trigger" onClick={onOpenNav} aria-label="Çalışma navigasyonunu aç">
          <Menu size={20} />
        </button>
        <div>
          <div className="breadcrumb">
            <span>Çalışmalar</span>
            <ChevronRight size={13} />
            <span>Ünite 200 HAZOP</span>
          </div>
          <div className="title-line">
            <h1>Besleme pompası P-101</h1>
            <span className="equipment-tag">Santrifüj pompa</span>
          </div>
        </div>
      </div>
      <div className="top-actions">
        <span className="save-state">
          <Check size={14} />
          Tüm değişiklikler kaydedildi
        </span>
        <button className="secondary-button">
          <History size={16} />
          Geçmiş
        </button>
        <button className="primary-button" onClick={onExport}>
          <Download size={16} />
          Rapor oluştur
        </button>
        <button className="icon-button" aria-label="Diğer çalışma işlemleri">
          <MoreHorizontal size={19} />
        </button>
      </div>
    </header>
  );
}

function WorksheetToolbar({
  onAddRow,
  evidenceOpen,
  onToggleEvidence,
}: {
  onAddRow: () => void;
  evidenceOpen: boolean;
  onToggleEvidence: () => void;
}) {
  return (
    <div className="worksheet-toolbar">
      <div className="toolbar-group">
        <button className="secondary-button compact" onClick={onAddRow}>
          <Plus size={16} />
          Satır ekle
        </button>
        <button className="secondary-button compact">
          <Archive size={16} />
          Kütüphaneden ekle
        </button>
        <span className="toolbar-divider" />
        <label className="table-search">
          <Search size={15} />
          <span className="sr-only">Çalışma sayfasında ara</span>
          <input placeholder="Çalışma sayfasında ara" />
        </label>
      </div>
      <div className="toolbar-group">
        <button className="secondary-button compact">
          <Table2 size={16} />
          Sütunlar
        </button>
        <button
          className={`evidence-toggle ${evidenceOpen ? "is-active" : ""}`}
          onClick={onToggleEvidence}
          aria-pressed={evidenceOpen}
        >
          <Sparkles size={16} />
          Kaynaklı öneriler
          <span>3</span>
        </button>
      </div>
    </div>
  );
}

function HazopTable({
  rows,
  selectedRow,
  onSelectRow,
  onUpdateRow,
}: {
  rows: HazopRow[];
  selectedRow: number;
  onSelectRow: (id: number) => void;
  onUpdateRow: (id: number, field: keyof HazopRow, value: string) => void;
}) {
  return (
    <div className="table-frame">
      <table className="hazop-table">
        <thead>
          <tr>
            <th className="row-index">#</th>
            <th className="col-guideword">Kılavuz kelime</th>
            <th className="col-deviation">Sapma</th>
            <th className="col-text">Neden</th>
            <th className="col-text">Sonuç</th>
            <th className="col-text">Mevcut önlemler</th>
            <th className="col-score">S</th>
            <th className="col-score">O</th>
            <th className="col-risk">Risk</th>
            <th className="col-status">İnceleme</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr
              key={row.id}
              className={row.id === selectedRow ? "is-selected" : ""}
              onClick={() => onSelectRow(row.id)}
            >
              <td className="row-index">
                <button
                  className="row-selector"
                  aria-label={`${index + 1}. satırı seç`}
                  aria-pressed={row.id === selectedRow}
                >
                  {index + 1}
                </button>
              </td>
              <td>
                <select
                  aria-label={`${index + 1}. satır kılavuz kelimesi`}
                  value={row.guideword}
                  onChange={(event) => onUpdateRow(row.id, "guideword", event.target.value)}
                >
                  <option>Yok</option>
                  <option>Fazla</option>
                  <option>Az</option>
                  <option>Ters</option>
                  <option>Başka</option>
                </select>
              </td>
              <td>
                <textarea
                  aria-label={`${index + 1}. satır sapması`}
                  value={row.deviation}
                  onChange={(event) => onUpdateRow(row.id, "deviation", event.target.value)}
                />
              </td>
              <td>
                <textarea
                  aria-label={`${index + 1}. satır nedeni`}
                  value={row.cause}
                  onChange={(event) => onUpdateRow(row.id, "cause", event.target.value)}
                />
              </td>
              <td>
                <textarea
                  aria-label={`${index + 1}. satır sonucu`}
                  value={row.consequence}
                  onChange={(event) => onUpdateRow(row.id, "consequence", event.target.value)}
                />
              </td>
              <td>
                <textarea
                  aria-label={`${index + 1}. satır mevcut önlemleri`}
                  value={row.safeguard}
                  onChange={(event) => onUpdateRow(row.id, "safeguard", event.target.value)}
                />
              </td>
              <td className="score-cell">{row.severity}</td>
              <td className="score-cell">{row.likelihood}</td>
              <td>
                <RiskBadge level={row.risk} />
              </td>
              <td>
                <StatusBadge status={row.status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function EvidencePanel({
  open,
  onClose,
  onApply,
}: {
  open: boolean;
  onClose: () => void;
  onApply: (suggestionId: string) => void;
}) {
  return (
    <aside className={`evidence-panel ${open ? "is-open" : ""}`} aria-label="Kaynaklı öneriler">
      <div className="evidence-header">
        <div>
          <div className="panel-title">
            <Sparkles size={18} />
            <h2>Kaynaklı öneriler</h2>
          </div>
          <p>Seçili satır: Akış yok</p>
        </div>
        <button className="icon-button" onClick={onClose} aria-label="Öneri panelini kapat">
          <PanelRightClose size={19} />
        </button>
      </div>

      <div className="grounding-note">
        <ShieldCheck size={17} />
        <span>Yalnızca erişilebilir çalışma ve standart kaynakları kullanıldı.</span>
      </div>

      <div className="suggestion-list">
        {suggestions.map((suggestion) => (
          <article className="suggestion-item" key={suggestion.id}>
            <div className="suggestion-meta">
              <span className={`suggestion-kind kind-${suggestion.target}`}>
                {suggestion.kind}
              </span>
              <span className="confidence">{suggestion.confidence} eşleşme</span>
            </div>
            <p>{suggestion.text}</p>
            <button className="citation-button" title={`${suggestion.source} · ${suggestion.section}`}>
              <FileClock size={14} />
              <span>
                <strong>{suggestion.source}</strong>
                {suggestion.section}
              </span>
              <ChevronRight size={14} />
            </button>
            <div className="suggestion-actions">
              <button className="text-button">Kaynağı aç</button>
              <button className="apply-button" onClick={() => onApply(suggestion.id)}>
                <Plus size={15} />
                Taslağa ekle
              </button>
            </div>
          </article>
        ))}
      </div>

      <div className="evidence-footer">
        <Bot size={18} />
        <div>
          <strong>İnsan incelemesi zorunlu</strong>
          <p>Öneriler karar değil, fasilitatör tarafından değerlendirilecek taslaklardır.</p>
        </div>
      </div>
    </aside>
  );
}

function LopaWorkspace() {
  const layers = [
    { name: "BPCS yüksek sıcaklık alarmı", pfd: "1.0E-1", valid: false, note: "Operatör müdahalesi bağımsızlık koşulunu karşılamıyor." },
    { name: "TSHH-204 bağımsız trip", pfd: "1.0E-2", valid: true, note: "Bağımsız sensör, logic solver ve son eleman." },
    { name: "Basınç tahliye vanası PSV-204", pfd: "1.0E-2", valid: true, note: "Yıllık test kaydı mevcut." },
  ];
  return (
    <section className="lopa-workspace">
      <div className="lopa-summary">
        <div>
          <span>Başlatıcı olay sıklığı</span>
          <strong className="mono">1.0E-1 /yıl</strong>
        </div>
        <ChevronRight size={18} />
        <div>
          <span>Toplam risk azaltma</span>
          <strong className="mono">1.0E-4</strong>
        </div>
        <ChevronRight size={18} />
        <div>
          <span>Sonuç sıklığı</span>
          <strong className="mono">1.0E-5 /yıl</strong>
        </div>
        <div className="sil-result">
          <span>Gerekli hedef</span>
          <strong>SIL 2</strong>
        </div>
      </div>
      <div className="section-heading">
        <div>
          <h2>Bağımsız koruma katmanları</h2>
          <p>Senaryo 02 · Yüksek akış sonucu reaktör sıcaklık yükselmesi</p>
        </div>
        <button className="secondary-button">
          <Plus size={16} />
          IPL ekle
        </button>
      </div>
      <div className="ipl-table">
        <div className="ipl-header">
          <span>Koruma katmanı</span>
          <span>Tipik PFD</span>
          <span>IPL uygunluğu</span>
          <span>Değerlendirme</span>
        </div>
        {layers.map((layer) => (
          <div className="ipl-row" key={layer.name}>
            <strong>{layer.name}</strong>
            <span className="mono">{layer.pfd}</span>
            <span className={layer.valid ? "ipl-valid" : "ipl-invalid"}>
              {layer.valid ? <CheckCircle2 size={15} /> : <AlertTriangle size={15} />}
              {layer.valid ? "Uygun" : "Kredi verilmedi"}
            </span>
            <p>{layer.note}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function RiskMatrix() {
  const labels = ["Çok düşük", "Düşük", "Olası", "Yüksek", "Çok yüksek"];
  return (
    <section className="matrix-workspace">
      <div className="section-heading">
        <div>
          <h2>Müşteri risk matrisi</h2>
          <p>ACWA Power 5 × 5 matrisi · Revizyon 3 · 12 Mayıs 2026</p>
        </div>
        <button className="secondary-button">Matrisi düzenle</button>
      </div>
      <div className="matrix-layout">
        <div className="matrix-y-label">Olasılık</div>
        <div className="matrix-grid" role="grid" aria-label="5 çarpı 5 risk matrisi">
          {[5, 4, 3, 2, 1].map((likelihood) =>
            [1, 2, 3, 4, 5].map((severity) => {
              const score = likelihood * severity;
              const level = score >= 16 ? "critical" : score >= 9 ? "high" : score >= 4 ? "medium" : "low";
              return (
                <button
                  key={`${likelihood}-${severity}`}
                  className={`matrix-cell matrix-${level}`}
                  aria-label={`Olasılık ${likelihood}, şiddet ${severity}, skor ${score}`}
                >
                  <strong>{score}</strong>
                  <span>{labels[Math.min(4, Math.floor((score - 1) / 5))]}</span>
                </button>
              );
            }),
          )}
        </div>
        <div className="matrix-x-label">Şiddet</div>
      </div>
    </section>
  );
}

function SourcesWorkspace() {
  return (
    <section className="sources-workspace">
      <div className="section-heading">
        <div>
          <h2>Çalışma kaynakları</h2>
          <p>Öneri motorunun bu çalışma için erişebildiği kontrollü bilgi tabanı.</p>
        </div>
        <button className="secondary-button">
          <Plus size={16} />
          Kaynak ekle
        </button>
      </div>
      <div className="source-list">
        {[
          ["IEC 61882:2016", "Standart", "42 bölüm", "12 Haz 2026"],
          ["IEC 61511-1:2016", "Standart", "67 bölüm", "12 Haz 2026"],
          ["HAZOP-2024-018 · Amin Ünitesi", "Geçmiş çalışma", "238 senaryo", "08 Haz 2026"],
          ["HAZOP-2023-041 · Tank Sahası", "Geçmiş çalışma", "184 senaryo", "08 Haz 2026"],
        ].map(([title, type, count, date]) => (
          <div className="source-row" key={title}>
            <span className="source-icon">
              <BookOpen size={18} />
            </span>
            <div>
              <strong>{title}</strong>
              <span>{type}</span>
            </div>
            <span>{count}</span>
            <span>İndekslendi · {date}</span>
            <button className="icon-button" aria-label={`${title} işlemleri`}>
              <MoreHorizontal size={18} />
            </button>
          </div>
        ))}
      </div>
    </section>
  );
}

export default function App() {
  const [activeTab, setActiveTab] = useState<WorkspaceTab>("HAZOP");
  const [rows, setRows] = useState(initialRows);
  const [selectedRow, setSelectedRow] = useState(1);
  const [evidenceOpen, setEvidenceOpen] = useState(true);
  const [navOpen, setNavOpen] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const selected = useMemo(
    () => rows.find((row) => row.id === selectedRow) ?? rows[0],
    [rows, selectedRow],
  );

  const notify = (message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(null), 2800);
  };

  const updateRow = (id: number, field: keyof HazopRow, value: string) => {
    setRows((current) =>
      current.map((row) => (row.id === id ? { ...row, [field]: value } : row)),
    );
  };

  const addRow = () => {
    const nextId = Math.max(...rows.map((row) => row.id)) + 1;
    setRows((current) => [
      ...current,
      {
        id: nextId,
        guideword: "Yok",
        deviation: "",
        cause: "",
        consequence: "",
        safeguard: "",
        severity: 1,
        likelihood: 1,
        risk: "Düşük",
        status: "Eksik",
      },
    ]);
    setSelectedRow(nextId);
    notify("Yeni HAZOP satırı eklendi.");
  };

  const applySuggestion = (suggestionId: string) => {
    const suggestion = suggestions.find((item) => item.id === suggestionId);
    if (!suggestion || !selected) return;
    const existing = selected[suggestion.target];
    updateRow(
      selected.id,
      suggestion.target,
      existing ? `${existing}\n${suggestion.text}` : suggestion.text,
    );
    notify(`${suggestion.kind} önerisi ${selected.id}. satır taslağına eklendi.`);
  };

  return (
    <div className="app-shell">
      <AppRail />
      <StudyNavigator open={navOpen} onClose={() => setNavOpen(false)} />
      <div className="workspace-shell">
        <TopBar
          onOpenNav={() => setNavOpen(true)}
          onExport={() => notify("Rapor kuyruğa alındı. DOCX ve PDF hazırlanıyor.")}
        />

        <main id="main-content" className="main-workspace">
          <div className="design-intent">
            <div>
              <span className="context-label">Tasarım niyeti</span>
              <p>
                T-100 hammadde tankından R-201 reaktörüne kesintisiz ve kontrollü besleme
                sağlamak.
              </p>
            </div>
            <button className="text-button">Node bilgilerini düzenle</button>
          </div>

          <div className="tab-bar" role="tablist" aria-label="Node çalışma alanları">
            {workspaceTabs.map((tab) => (
              <button
                key={tab.label}
                role="tab"
                aria-selected={activeTab === tab.label}
                className={activeTab === tab.label ? "is-active" : ""}
                onClick={() => setActiveTab(tab.label)}
              >
                {tab.label}
                {tab.count !== undefined && <span>{tab.count}</span>}
              </button>
            ))}
          </div>

          {activeTab === "HAZOP" && (
            <>
              <WorksheetToolbar
                onAddRow={addRow}
                evidenceOpen={evidenceOpen}
                onToggleEvidence={() => setEvidenceOpen((current) => !current)}
              />
              <div className={`hazop-layout ${evidenceOpen ? "with-evidence" : ""}`}>
                <HazopTable
                  rows={rows}
                  selectedRow={selectedRow}
                  onSelectRow={setSelectedRow}
                  onUpdateRow={updateRow}
                />
                <EvidencePanel
                  open={evidenceOpen}
                  onClose={() => setEvidenceOpen(false)}
                  onApply={applySuggestion}
                />
              </div>
            </>
          )}
          {activeTab === "LOPA" && <LopaWorkspace />}
          {activeTab === "Risk matrisi" && <RiskMatrix />}
          {activeTab === "Kaynaklar" && <SourcesWorkspace />}
        </main>

        <footer className="status-bar">
          <div>
            <Activity size={14} />
            <span>{rows.length} satır</span>
            <span className="status-separator" />
            <span>3 açık aksiyon</span>
            <span className="status-separator" />
            <span className="local-data">
              <ShieldCheck size={14} />
              Veri yerel ortamda
            </span>
          </div>
          <div className="shortcut-hints">
            <span><kbd>Ctrl</kbd><kbd>Enter</kbd> Satır ekle</span>
            <span><kbd>⌘</kbd><kbd>K</kbd> Komutlar</span>
          </div>
        </footer>
      </div>

      {toast && (
        <div className="toast" role="status">
          <CheckCircle2 size={18} />
          {toast}
        </div>
      )}
    </div>
  );
}
