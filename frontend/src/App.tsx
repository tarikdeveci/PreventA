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
  Cloud,
  Clock3,
  Download,
  FileClock,
  FileOutput,
  Files,
  Gauge,
  History,
  LayoutGrid,
  ListChecks,
  Menu,
  MoreHorizontal,
  PanelRightClose,
  Plus,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
  Table2,
  Trash2,
  X,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  addLopaLayer,
  createHazopRow,
  createNode,
  createStudy,
  deleteHazopRow,
  deleteLopaLayer,
  fetchLopaLayers,
  fetchNodes,
  fetchProductStatus,
  fetchRows,
  fetchStudies,
  reportUrl,
  updateHazopRow,
} from "./api";
import {
  fallbackStatus,
  fallbackStudy,
  type HazopRow,
  type LopaLayer,
  type ProductStatus,
  type StudyListItem,
  type Suggestion,
  type WorkspaceNode,
  type WorkspaceStudy,
} from "./data";

type WorkspaceTab = "HAZOP" | "LOPA" | "Risk matrisi" | "Kaynaklar" | "Ürün durumu";

function workspaceTabs(rowCount: number, lopaCount: number): { label: WorkspaceTab; count?: number }[] {
  return [
    { label: "HAZOP", count: rowCount || undefined },
    { label: "LOPA", count: lopaCount || undefined },
    { label: "Risk matrisi" },
    { label: "Kaynaklar" },
    { label: "Ürün durumu" },
  ];
}

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

type RailSection = "studies" | "library" | "reports" | "history";

function AppRail({
  active,
  onSelect,
}: {
  active: RailSection;
  onSelect: (section: RailSection) => void;
}) {
  return (
    <aside className="app-rail" aria-label="Ana uygulama">
      <button className="brand-mark" aria-label="PreventA ana sayfa">
        <ShieldCheck size={25} strokeWidth={2.2} />
      </button>
      <nav className="rail-nav" aria-label="Uygulama bölümleri">
        <button
          className={`rail-button ${active === "studies" ? "is-active" : ""}`}
          aria-label="Çalışmalar"
          title="Çalışmalar"
          onClick={() => onSelect("studies")}
        >
          <Files size={20} />
        </button>
        <button
          className={`rail-button ${active === "library" ? "is-active" : ""}`}
          aria-label="Senaryo kütüphanesi"
          title="Senaryo kütüphanesi"
          onClick={() => onSelect("library")}
        >
          <BookOpen size={20} />
        </button>
        <button
          className={`rail-button ${active === "reports" ? "is-active" : ""}`}
          aria-label="Raporlar"
          title="Raporlar"
          onClick={() => onSelect("reports")}
        >
          <FileOutput size={20} />
        </button>
        <button
          className={`rail-button ${active === "history" ? "is-active" : ""}`}
          aria-label="Denetim geçmişi"
          title="Denetim geçmişi"
          onClick={() => onSelect("history")}
        >
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
        <button className="avatar-button" aria-label="Kullanıcı hesabı" title="Kullanıcı">
          P
        </button>
      </div>
    </aside>
  );
}

function StudyNavigator({
  open,
  onClose,
  nodes,
  study,
  activeNodeId,
  onSelectNode,
  onCreateNode,
  studies,
  onSelectStudy,
}: {
  open: boolean;
  onClose: () => void;
  nodes: WorkspaceNode[];
  study: WorkspaceStudy;
  activeNodeId: string;
  onSelectNode: (id: string) => void;
  onCreateNode: () => void;
  studies: StudyListItem[];
  onSelectStudy: (studyId: string) => void;
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
            <strong>{study.title}</strong>
          </div>
          <button className="icon-button mobile-only" onClick={onClose} aria-label="Navigasyonu kapat">
            <X size={18} />
          </button>
        </div>

        <div className="study-switcher">
          <span className="study-monogram">RA</span>
          <span>
            <label className="sr-only" htmlFor="study-selector">Aktif çalışmayı seç</label>
            <select
              id="study-selector"
              value={study.id}
              onChange={(event) => onSelectStudy(event.target.value)}
            >
              {studies.map((item) => (
                <option value={item.id} key={item.id}>{item.title}</option>
              ))}
            </select>
            <small>{study.client} · {study.facility}</small>
          </span>
          <ChevronDown size={16} />
        </div>

        <div className="nav-section">
          <div className="nav-section-title">
            <span>Çalışma yapısı</span>
            <button className="compact-icon" aria-label="Yeni node ekle" onClick={onCreateNode}>
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
            <span className="nav-count">{nodes.length}</span>
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
                className={`node-row ${node.id === activeNodeId ? "is-active" : ""}`}
                key={node.id}
                onClick={() => onSelectNode(node.id)}
              >
                <span className={`node-state node-state-${node.state}`} aria-hidden="true" />
                <span className="node-copy">
                  <small>{node.code}</small>
                  <strong>{node.name}</strong>
                </span>
                <span className="node-count">{node.scenario_count}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="study-nav-footer">
          <div className="progress-copy">
            <span>Çalışma ilerlemesi</span>
            <strong>%{study.progress}</strong>
          </div>
          <div className="progress-track" aria-label="Çalışma ilerlemesi yüzde 62">
            <span style={{ width: `${study.progress}%` }} />
          </div>
          <small>
            {study.reviewed_scenarios} / {study.total_scenarios} senaryo incelendi
          </small>
        </div>
      </aside>
    </>
  );
}

function TopBar({
  onOpenNav,
  onExport,
  activeNode,
  studyTitle,
  apiConnected,
}: {
  onOpenNav: () => void;
  onExport: () => void;
  activeNode: WorkspaceNode;
  studyTitle: string;
  apiConnected: boolean;
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
            <span>{studyTitle}</span>
          </div>
          <div className="title-line">
            <h1>{activeNode.name}</h1>
            <span className="equipment-tag">{activeNode.equipment_type}</span>
          </div>
        </div>
      </div>
      <div className="top-actions">
        <span className={`api-state ${apiConnected ? "is-connected" : "is-fallback"}`}>
          <Cloud size={14} />
          {apiConnected ? "API bağlı" : "Fallback veri"}
        </span>
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
  onDeleteRow,
  evidenceOpen,
  onToggleEvidence,
}: {
  onAddRow: () => void;
  onDeleteRow: () => void;
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
        <button className="secondary-button compact danger-action" onClick={onDeleteRow}>
          <Trash2 size={16} />
          Satırı sil
        </button>
        <button className="secondary-button compact" disabled title="Yakında">
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
              <td className="score-cell">
                <select
                  aria-label={`${index + 1}. satır şiddet`}
                  value={row.severity}
                  onChange={(event) => onUpdateRow(row.id, "severity", event.target.value)}
                >
                  {[1, 2, 3, 4, 5].map((v) => <option key={v} value={v}>{v}</option>)}
                </select>
              </td>
              <td className="score-cell">
                <select
                  aria-label={`${index + 1}. satır olasılık`}
                  value={row.likelihood}
                  onChange={(event) => onUpdateRow(row.id, "likelihood", event.target.value)}
                >
                  {[1, 2, 3, 4, 5].map((v) => <option key={v} value={v}>{v}</option>)}
                </select>
              </td>
              <td>
                <RiskBadge level={row.risk} />
              </td>
              <td>
                <select
                  aria-label={`${index + 1}. satır inceleme durumu`}
                  value={row.status}
                  className={`status-select status-${row.status.toLocaleLowerCase("tr")}`}
                  onChange={(event) => onUpdateRow(row.id, "status", event.target.value)}
                >
                  <option>Eksik</option>
                  <option>Taslak</option>
                  <option>İncelendi</option>
                </select>
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
  suggestions,
}: {
  open: boolean;
  onClose: () => void;
  onApply: (suggestionId: string) => void;
  suggestions: Suggestion[];
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

function LopaWorkspace({ selectedRow }: { selectedRow: HazopRow | undefined }) {
  const [layers, setLayers] = useState<LopaLayer[]>([]);
  const [loading, setLoading] = useState(false);
  const [addOpen, setAddOpen] = useState(false);
  const [form, setForm] = useState({ description: "", pfd: "1.0e-2", is_valid: true, note: "" });

  useEffect(() => {
    if (!selectedRow) {
      setLayers([]);
      return;
    }
    setLoading(true);
    fetchLopaLayers(selectedRow.id)
      .then(setLayers)
      .catch(() => setLayers([]))
      .finally(() => setLoading(false));
  }, [selectedRow?.id]);

  const handleAdd = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!selectedRow) return;
    const layer = await addLopaLayer(selectedRow.id, {
      description: form.description,
      pfd: parseFloat(form.pfd),
      is_valid: form.is_valid,
      note: form.note,
    });
    setLayers((current) => [...current, layer]);
    setForm({ description: "", pfd: "1.0e-2", is_valid: true, note: "" });
    setAddOpen(false);
  };

  const handleDelete = async (layerId: string) => {
    if (!window.confirm("Bu IPL kaydı silinsin mi?")) return;
    await deleteLopaLayer(layerId);
    setLayers((current) => current.filter((l) => l.id !== layerId));
  };

  const initiatorFreq = 0.1;
  const totalReduction = layers.filter((l) => l.is_valid).reduce((acc, l) => acc * l.pfd, 1);
  const outcomeFreq = initiatorFreq * totalReduction;

  return (
    <section className="lopa-workspace">
      <div className="lopa-summary">
        <div>
          <span>Başlatıcı olay sıklığı</span>
          <strong className="mono">{initiatorFreq.toExponential(1)} /yıl</strong>
        </div>
        <ChevronRight size={18} />
        <div>
          <span>Toplam risk azaltma</span>
          <strong className="mono">{totalReduction.toExponential(1)}</strong>
        </div>
        <ChevronRight size={18} />
        <div>
          <span>Sonuç sıklığı</span>
          <strong className="mono">{outcomeFreq.toExponential(1)} /yıl</strong>
        </div>
        <div className="sil-result">
          <span>Seçili senaryo</span>
          <strong>{selectedRow ? `Satır ${selectedRow.id}` : "—"}</strong>
        </div>
      </div>
      <div className="section-heading">
        <div>
          <h2>Bağımsız koruma katmanları</h2>
          <p>
            {selectedRow
              ? `Senaryo: ${selectedRow.deviation || "Sapmayı tanımlayın"}`
              : "HAZOP sekmesinden bir satır seçin."}
          </p>
        </div>
        <button className="secondary-button" onClick={() => setAddOpen(true)} disabled={!selectedRow}>
          <Plus size={16} />
          IPL ekle
        </button>
      </div>

      {loading ? (
        <div className="table-loading">IPL katmanları yükleniyor...</div>
      ) : layers.length === 0 ? (
        <div className="table-empty">
          <CheckCircle2 size={28} />
          <strong>Bu senaryo için henüz IPL kaydı yok</strong>
          <p>Koruma katmanını eklemek için "IPL ekle" düğmesini kullanın.</p>
        </div>
      ) : (
        <div className="ipl-table">
          <div className="ipl-header">
            <span>Koruma katmanı</span>
            <span>Tipik PFD</span>
            <span>IPL uygunluğu</span>
            <span>Değerlendirme</span>
            <span />
          </div>
          {layers.map((layer) => (
            <div className="ipl-row" key={layer.id}>
              <strong>{layer.description}</strong>
              <span className="mono">{layer.pfd.toExponential(1)}</span>
              <span className={layer.is_valid ? "ipl-valid" : "ipl-invalid"}>
                {layer.is_valid ? <CheckCircle2 size={15} /> : <AlertTriangle size={15} />}
                {layer.is_valid ? "Uygun" : "Kredi verilmedi"}
              </span>
              <p>{layer.note}</p>
              <button
                className="icon-button"
                aria-label="IPL sil"
                onClick={() => handleDelete(layer.id)}
              >
                <Trash2 size={15} />
              </button>
            </div>
          ))}
        </div>
      )}

      {addOpen && (
        <div className="modal-backdrop" role="presentation">
          <form className="form-dialog" onSubmit={handleAdd}>
            <div className="dialog-heading">
              <div><h2>IPL ekle</h2><p>Bağımsız koruma katmanı bilgilerini girin.</p></div>
              <button type="button" className="icon-button" onClick={() => setAddOpen(false)} aria-label="Kapat"><X size={18} /></button>
            </div>
            <label>Tanım<input required value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></label>
            <label>PFD (örn: 1e-2)<input required value={form.pfd} onChange={(e) => setForm({ ...form, pfd: e.target.value })} /></label>
            <label>
              <input type="checkbox" checked={form.is_valid} onChange={(e) => setForm({ ...form, is_valid: e.target.checked })} />
              {" "}IPL uygunluk kriterini karşılıyor
            </label>
            <label>Not<textarea value={form.note} onChange={(e) => setForm({ ...form, note: e.target.value })} /></label>
            <div className="dialog-actions">
              <button type="button" className="secondary-button" onClick={() => setAddOpen(false)}>Vazgeç</button>
              <button className="primary-button">Kaydet</button>
            </div>
          </form>
        </div>
      )}
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

function ProductStatusWorkspace({ status }: { status: ProductStatus }) {
  const statusCopy = {
    complete: "Tamamlandı",
    in_progress: "Devam ediyor",
    planned: "Planlandı",
  } as const;

  return (
    <section className="delivery-workspace">
      <div className="delivery-hero">
        <div className="delivery-summary">
          <span className="context-label">{status.release}</span>
          <h2>{status.stage}</h2>
          <p>
            Arayüz canlı API'ye bağlı. Kalıcı PostgreSQL CRUD, canlı Ollama corpus'u ve
            rapor üretimi tamamlanmadan ürün pilot kullanıma hazır sayılmayacak.
          </p>
          <div className="delivery-progress-row">
            <div className="delivery-progress-track">
              <span style={{ width: `${status.overall_progress}%` }} />
            </div>
            <strong>%{status.overall_progress}</strong>
          </div>
        </div>
        <dl className="runtime-facts">
          <div>
            <dt>API</dt>
            <dd className={status.api_connected ? "fact-ok" : "fact-warn"}>
              {status.api_connected ? "Bağlı" : "Bağlantı yok"}
            </dd>
          </div>
          <div>
            <dt>Veri kalıcılığı</dt>
            <dd className={status.persistence === "postgresql" ? "fact-ok" : "fact-warn"}>
              {status.persistence === "postgresql"
                ? "PostgreSQL"
                : status.persistence === "volatile_sqlite"
                  ? "Geçici SQLite"
                  : "API seed"}
            </dd>
          </div>
          <div>
            <dt>AI çalışma zamanı</dt>
            <dd className={status.ai_runtime === "ollama_connected" ? "fact-ok" : "fact-warn"}>
              {status.ai_runtime === "ollama_connected" ? "Ollama bağlı" : "Sözleşme hazır"}
            </dd>
          </div>
          <div>
            <dt>Deploy</dt>
            <dd>{status.deployment}</dd>
          </div>
        </dl>
      </div>

      <div className="section-heading delivery-heading">
        <div>
          <h2>Modül teslim durumu</h2>
          <p>PRD kabul kriterlerine göre mevcut teknik ilerleme.</p>
        </div>
      </div>
      <div className="delivery-list">
        {status.modules.map((module) => (
          <article className="delivery-row" key={module.id}>
            <span className={`delivery-icon status-${module.status}`}>
              {module.status === "complete" ? (
                <CheckCircle2 size={18} />
              ) : module.status === "in_progress" ? (
                <Activity size={18} />
              ) : (
                <Clock3 size={18} />
              )}
            </span>
            <div className="delivery-copy">
              <div>
                <strong>{module.name}</strong>
                <span className={`delivery-status status-${module.status}`}>
                  {statusCopy[module.status]}
                </span>
              </div>
              <p>{module.detail}</p>
            </div>
            <div className="module-progress">
              <span style={{ width: `${module.progress}%` }} />
            </div>
            <strong className="module-percent">%{module.progress}</strong>
          </article>
        ))}
      </div>

      <div className="next-milestone">
        <ListChecks size={20} />
        <div>
          <strong>Sıradaki gerçek kilometre taşı</strong>
          <p>
            Study, node ve worksheet create/update endpoint'lerini PostgreSQL'e bağlamak;
            ardından aynı akışla ilk gerçek pilot çalışmayı kaydetmek.
          </p>
        </div>
      </div>
    </section>
  );
}

function LandingPage() {
  return (
    <div className="landing-page">
      <header className="landing-nav">
        <a className="landing-brand" href="/">
          <ShieldCheck size={28} />
          <span>PreventA</span>
        </a>
        <nav aria-label="Landing navigasyonu">
          <a href="#urun">Ürün</a>
          <a href="#guvenlik">Veri güvenliği</a>
          <a href="#akis">İş akışı</a>
        </nav>
        <a className="primary-button landing-login" href="/app">
          Çalışma alanını aç
        </a>
      </header>

      <main>
        <section className="landing-hero">
          <div className="hero-copy">
            <span className="hero-kicker">HAZOP · LOPA · Kurumsal tehlike hafızası</span>
            <h1>Proses güvenliği çalışmalarını tekrar kullanılabilir bilgiye dönüştürün.</h1>
            <p>
              PreventA, fasilitatörlerin HAZOP ve LOPA çalışmalarını yapılandırılmış
              biçimde yürütmesini, geçmiş senaryolardan kaynaklı öneriler almasını ve
              müşteri raporunu aynı çalışma alanından üretmesini sağlar.
            </p>
            <div className="hero-actions">
              <a className="primary-button landing-cta" href="/app">
                MVP çalışma alanını aç
                <ChevronRight size={17} />
              </a>
              <a className="secondary-button landing-cta" href="#akis">
                İş akışını incele
              </a>
            </div>
            <div className="hero-trust">
              <span><ShieldCheck size={16} /> Yerel veri seçeneği</span>
              <span><FileClock size={16} /> Kaynak ve değişiklik izi</span>
              <span><Download size={16} /> DOCX rapor çıktısı</span>
            </div>
          </div>
          <div className="hero-product" aria-label="PreventA ürün önizlemesi">
            <div className="mini-window-bar">
              <span />
              <span />
              <span />
              <strong>Ünite 200 HAZOP</strong>
            </div>
            <div className="mini-workspace">
              <div className="mini-sidebar">
                <span className="mini-node complete">N-01</span>
                <span className="mini-node active">N-02</span>
                <span className="mini-node">N-03</span>
                <span className="mini-node">N-04</span>
              </div>
              <div className="mini-table">
                <div className="mini-table-head">
                  <span>Sapma</span><span>Neden</span><span>Sonuç</span><span>Risk</span>
                </div>
                {["Akış yok", "Yüksek akış", "Ters akış", "Düşük akış"].map((item, index) => (
                  <div className="mini-table-row" key={item}>
                    <strong>{item}</strong>
                    <span />
                    <span />
                    <em className={`mini-risk risk-${index}`}>{index === 2 ? "Kritik" : "Orta"}</em>
                  </div>
                ))}
              </div>
              <div className="mini-evidence">
                <strong>Kaynaklı öneriler</strong>
                <div><Sparkles size={14} /> Çekvalf arızası</div>
                <div><Sparkles size={14} /> Düşük akış alarmı</div>
                <div><Sparkles size={14} /> IEC 61882 §6.3</div>
              </div>
            </div>
          </div>
        </section>

        <section className="landing-section" id="urun">
          <div className="landing-section-heading">
            <h2>Toplantı boyunca tek çalışma yüzeyi</h2>
            <p>
              Study yapısı, worksheet, risk değerlendirmesi, LOPA ve kanıtlar aynı
              bağlamda kalır.
            </p>
          </div>
          <div className="capability-list">
            {[
              ["01", "Klavye odaklı HAZOP", "Satırları hızla oluşturun, düzenleyin ve risk derecesini otomatik hesaplayın."],
              ["02", "Kaynaklı öneriler", "Geçmiş çalışmalar ve standartlardan gelen önerilerin kaynağını inceleyin."],
              ["03", "LOPA ve IPL kaydı", "Koruma katmanlarını PFD ve uygunluk değerlendirmesiyle senaryoya bağlayın."],
              ["04", "Teslim edilebilir rapor", "Çalışmayı tek tıkla düzenlenebilir DOCX raporuna dönüştürün."],
            ].map(([number, title, detail]) => (
              <article key={number}>
                <span>{number}</span>
                <h3>{title}</h3>
                <p>{detail}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="security-section" id="guvenlik">
          <div>
            <ShieldCheck size={34} />
            <h2>Hassas tesis verisi için açık mimari sınırlar</h2>
          </div>
          <p>
            PreventA, öneri ve veri katmanlarını ayrı sözleşmelerle yönetir. Üretim
            kurulumunda PostgreSQL ve Ollama müşteri ortamında çalıştırılabilir; model
            önerileri mühendis onayı olmadan çalışma kararına dönüşmez.
          </p>
        </section>

        <section className="workflow-section" id="akis">
          <h2>Bir çalışmanın PreventA akışı</h2>
          <ol>
            <li><strong>Study açın</strong><span>Müşteri, tesis ve risk bağlamını kaydedin.</span></li>
            <li><strong>Node'ları tanımlayın</strong><span>Ekipman tipi ve tasarım niyetini standardize edin.</span></li>
            <li><strong>HAZOP ve LOPA'yı yürütün</strong><span>Senaryoları kaydedin, kaynaklı önerileri inceleyin.</span></li>
            <li><strong>Raporu teslim edin</strong><span>Denetim iziyle birlikte DOCX çıktısını indirin.</span></li>
          </ol>
          <a className="primary-button landing-cta" href="/app">Çalışma alanına geç</a>
        </section>
      </main>
      <footer className="landing-footer">
        <span>PreventA · Process Safety Workspace</span>
        <span>MVP · Haziran 2026</span>
      </footer>
    </div>
  );
}

function CreateStudyDialog({
  open,
  onClose,
  onCreated,
  onError,
}: {
  open: boolean;
  onClose: () => void;
  onCreated: (study: StudyListItem) => void;
  onError: (msg: string) => void;
}) {
  const [values, setValues] = useState({ title: "", client: "", facility: "" });
  const [saving, setSaving] = useState(false);
  if (!open) return null;
  return (
    <div className="modal-backdrop" role="presentation">
      <form
        className="form-dialog"
        onSubmit={async (event) => {
          event.preventDefault();
          setSaving(true);
          try {
            const created = await createStudy(values);
            onCreated(created);
          } catch {
            onError("Çalışma oluşturulamadı. API bağlantısını kontrol edin.");
          } finally {
            setSaving(false);
          }
        }}
      >
        <div className="dialog-heading">
          <div><h2>Yeni çalışma</h2><p>Müşteri ve tesis bağlamını tanımlayın.</p></div>
          <button type="button" className="icon-button" onClick={onClose} aria-label="Kapat"><X size={18} /></button>
        </div>
        <label>Çalışma adı<input required value={values.title} onChange={(e) => setValues({...values, title: e.target.value})} /></label>
        <label>Müşteri<input required value={values.client} onChange={(e) => setValues({...values, client: e.target.value})} /></label>
        <label>Tesis<input required value={values.facility} onChange={(e) => setValues({...values, facility: e.target.value})} /></label>
        <div className="dialog-actions">
          <button type="button" className="secondary-button" onClick={onClose}>Vazgeç</button>
          <button className="primary-button" disabled={saving}>{saving ? "Oluşturuluyor" : "Çalışma oluştur"}</button>
        </div>
      </form>
    </div>
  );
}

function CreateNodeDialog({
  open,
  studyId,
  onClose,
  onCreated,
  onError,
}: {
  open: boolean;
  studyId: string;
  onClose: () => void;
  onCreated: (node: WorkspaceNode) => void;
  onError: (msg: string) => void;
}) {
  const [values, setValues] = useState({ code: "", name: "", equipment_type: "", design_intent: "" });
  const [saving, setSaving] = useState(false);
  if (!open) return null;
  return (
    <div className="modal-backdrop" role="presentation">
      <form
        className="form-dialog"
        onSubmit={async (event) => {
          event.preventDefault();
          setSaving(true);
          try {
            onCreated(await createNode(studyId, values));
          } catch {
            onError("Node oluşturulamadı. API bağlantısını kontrol edin.");
          } finally {
            setSaving(false);
          }
        }}
      >
        <div className="dialog-heading">
          <div><h2>Yeni node</h2><p>Öneri kalitesi için ekipman tipini açık yazın.</p></div>
          <button type="button" className="icon-button" onClick={onClose} aria-label="Kapat"><X size={18} /></button>
        </div>
        <label>Node kodu<input required placeholder="N-06" value={values.code} onChange={(e) => setValues({...values, code: e.target.value})} /></label>
        <label>Node adı<input required value={values.name} onChange={(e) => setValues({...values, name: e.target.value})} /></label>
        <label>Ekipman tipi<input required value={values.equipment_type} onChange={(e) => setValues({...values, equipment_type: e.target.value})} /></label>
        <label>Tasarım niyeti<textarea required value={values.design_intent} onChange={(e) => setValues({...values, design_intent: e.target.value})} /></label>
        <div className="dialog-actions">
          <button type="button" className="secondary-button" onClick={onClose}>Vazgeç</button>
          <button className="primary-button" disabled={saving}>{saving ? "Oluşturuluyor" : "Node oluştur"}</button>
        </div>
      </form>
    </div>
  );
}

function WorkspaceApp() {
  const [activeTab, setActiveTab] = useState<WorkspaceTab>("HAZOP");
  const [railSection, setRailSection] = useState<RailSection>("studies");
  const [rows, setRows] = useState<HazopRow[]>([]);
  const [lopaLayerCount, setLopaLayerCount] = useState(0);
  const [workspaceNodes, setWorkspaceNodes] = useState<WorkspaceNode[]>([]);
  const [study, setStudy] = useState(fallbackStudy);
  const [studyOptions, setStudyOptions] = useState<StudyListItem[]>([]);
  const [workspaceSuggestions] = useState<Suggestion[]>([]);
  const [productStatus, setProductStatus] = useState(fallbackStatus);
  const [apiConnected, setApiConnected] = useState(false);
  const [activeNodeId, setActiveNodeId] = useState("");
  const [studyDialogOpen, setStudyDialogOpen] = useState(false);
  const [nodeDialogOpen, setNodeDialogOpen] = useState(false);
  const [loadingRows, setLoadingRows] = useState(false);
  const [selectedRow, setSelectedRow] = useState(1);
  const [evidenceOpen, setEvidenceOpen] = useState(true);
  const [navOpen, setNavOpen] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);
  const saveTimers = useRef<Record<string, number>>({});

  const selected = useMemo(
    () => rows.find((row) => row.id === selectedRow) ?? rows[0],
    [rows, selectedRow],
  );
  const activeNode = useMemo(
    () =>
      workspaceNodes.find((node) => node.id === activeNodeId) ??
      workspaceNodes[0] ??
      {
        id: "",
        code: "",
        name: "Node seçilmedi",
        equipment_type: "Çalışma bekleniyor",
        design_intent: "Başlamak için bir çalışma ve node seçin.",
        scenario_count: 0,
        state: "empty" as const,
      },
    [activeNodeId, workspaceNodes],
  );

  useEffect(() => {
    let active = true;
    Promise.all([fetchProductStatus(), fetchStudies()])
      .then(async ([status, studies]) => {
        if (!active) return;
        setProductStatus(status);
        setApiConnected(status.api_connected);
        setStudyOptions(studies);
        const firstStudy = studies[0];
        if (!firstStudy) {
          setRows([]);
          setWorkspaceNodes([]);
          setActiveNodeId("");
          return;
        }

        setStudy({
          ...firstStudy,
          progress: 0,
          reviewed_scenarios: 0,
          total_scenarios: 0,
        });
        const studyNodes = await fetchNodes(firstStudy.id);
        if (!active) return;
        setWorkspaceNodes(studyNodes);
        const firstNode = studyNodes[0];
        if (!firstNode) {
          setRows([]);
          setActiveNodeId("");
          return;
        }
        setActiveNodeId(firstNode.id);
        const nodeRows = await fetchRows(firstNode.id);
        if (!active) return;
        setRows(nodeRows);
        setSelectedRow(nodeRows[0]?.id ?? 0);
      })
      .catch(() => {
        if (!active) return;
        setApiConnected(false);
        setProductStatus(fallbackStatus);
      });
    return () => {
      active = false;
    };
  }, []);

  // Keyboard shortcut: Ctrl+Enter to add row
  const addRowRef = useRef<() => Promise<void>>();
  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
        event.preventDefault();
        addRowRef.current?.();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  const notify = (message: string, type: "success" | "error" = "success") => {
    setToast({ message, type });
    window.setTimeout(() => setToast(null), 2800);
  };

  const updateRow = (id: number, field: keyof HazopRow, value: string) => {
    setRows((current) =>
      current.map((row) => (row.id === id ? { ...row, [field]: value } : row)),
    );
    const timerKey = `${id}:${field}`;
    window.clearTimeout(saveTimers.current[timerKey]);
    saveTimers.current[timerKey] = window.setTimeout(async () => {
      try {
        const saved = await updateHazopRow(id, { [field]: value });
        setRows((current) =>
          current.map((row) =>
            row.id === id
              ? { ...row, [field]: saved[field], risk: saved.risk }
              : row,
          ),
        );
        setApiConnected(true);
      } catch {
        setApiConnected(false);
        notify("Değişiklik yerel taslakta kaldı. API bağlantısını kontrol edin.", "error");
      }
    }, 550);
  };

  const addRow = async () => {
    if (!activeNodeId) {
      notify("Satır eklemek için önce bir node oluşturun.", "error");
      return;
    }
    try {
      const created = await createHazopRow(activeNodeId);
      setRows((current) => [...current, created]);
      setSelectedRow(created.id);
      notify("Yeni HAZOP satırı veritabanına eklendi.");
    } catch {
      notify("Satır oluşturulamadı. API bağlantısını kontrol edin.", "error");
    }
  };

  // Keep ref in sync so keyboard handler can call latest addRow
  useEffect(() => { addRowRef.current = addRow; });

  const removeSelectedRow = async () => {
    if (!selected) return;
    if (!window.confirm("Seçili HAZOP satırı kalıcı olarak silinsin mi?")) return;
    try {
      await deleteHazopRow(selected.id);
      const remaining = rows.filter((row) => row.id !== selected.id);
      setRows(remaining);
      setSelectedRow(remaining[0]?.id ?? 0);
      notify("HAZOP satırı silindi.");
    } catch {
      notify("Satır silinemedi.", "error");
    }
  };

  const selectNode = async (nodeId: string) => {
    setActiveNodeId(nodeId);
    setNavOpen(false);
    setLoadingRows(true);
    try {
      const nodeRows = await fetchRows(nodeId);
      setRows(nodeRows);
      setSelectedRow(nodeRows[0]?.id ?? 0);
      setApiConnected(true);
    } catch {
      setRows([]);
      setApiConnected(false);
    } finally {
      setLoadingRows(false);
    }
  };

  const selectStudy = async (studyId: string) => {
    const selectedStudy = studyOptions.find((item) => item.id === studyId);
    if (!selectedStudy) return;
    setStudy((current) => ({
      ...current,
      ...selectedStudy,
      progress: 0,
      reviewed_scenarios: 0,
      total_scenarios: 0,
    }));
    setLoadingRows(true);
    try {
      const studyNodes = await fetchNodes(studyId);
      setWorkspaceNodes(studyNodes);
      const firstNode = studyNodes[0];
      if (firstNode) {
        setActiveNodeId(firstNode.id);
        const nodeRows = await fetchRows(firstNode.id);
        setRows(nodeRows);
        setSelectedRow(nodeRows[0]?.id ?? 0);
      } else {
        setRows([]);
        setActiveNodeId("");
      }
      setApiConnected(true);
    } catch {
      setRows([]);
      setWorkspaceNodes([]);
      setActiveNodeId("");
      setApiConnected(false);
      notify("Çalışma yüklenemedi. API bağlantısını kontrol edin.", "error");
    } finally {
      setLoadingRows(false);
    }
  };

  const applySuggestion = (suggestionId: string) => {
    const suggestion = workspaceSuggestions.find((item) => item.id === suggestionId);
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
      <AppRail active={railSection} onSelect={setRailSection} />
      <StudyNavigator
        open={navOpen}
        onClose={() => setNavOpen(false)}
        nodes={workspaceNodes}
        study={study}
        activeNodeId={activeNodeId}
        onSelectNode={selectNode}
        onCreateNode={() => setNodeDialogOpen(true)}
        studies={studyOptions}
        onSelectStudy={selectStudy}
      />
      <div className="workspace-shell">
        <TopBar
          onOpenNav={() => setNavOpen(true)}
          onExport={() => {
            window.location.href = reportUrl(study.id, activeNode.id);
          }}
          activeNode={activeNode}
          studyTitle={study.title}
          apiConnected={apiConnected}
        />

        <main id="main-content" className="main-workspace">
          {railSection !== "studies" ? (
            <section className="rail-section-page">
              <div className="section-heading">
                <div>
                  <h2>
                    {railSection === "library"
                      ? "Senaryo kütüphanesi"
                      : railSection === "reports"
                        ? "Raporlar"
                        : "Denetim geçmişi"}
                  </h2>
                  <p>
                    {railSection === "library"
                      ? "Onaylanmış neden, sonuç ve önlem kayıtlarını ekipman tipine göre yönetin."
                      : railSection === "reports"
                        ? "Çalışmalardan üretilen DOCX raporlarını indirin."
                        : "Study, node ve worksheet değişikliklerinin audit kaydı."}
                  </p>
                </div>
                {railSection === "reports" && (
                  <button className="primary-button" onClick={() => { window.location.href = reportUrl(study.id, activeNode.id); }}>
                    <Download size={16} /> Aktif node raporunu indir
                  </button>
                )}
              </div>
              <div className="functional-empty">
                {railSection === "library" ? <BookOpen size={28} /> : railSection === "reports" ? <FileOutput size={28} /> : <History size={28} />}
                <strong>{railSection === "history" ? "Audit kayıtları backend'de tutuluyor" : "Bu modül MVP akışına bağlı"}</strong>
                <p>
                  {railSection === "library"
                    ? `${workspaceSuggestions.length} kaynaklı öneri aktif çalışma bağlamında kullanılabilir.`
                    : railSection === "reports"
                      ? "Rapor düğmesi canlı API üzerinden düzenlenebilir DOCX üretir."
                      : "Create, update ve delete işlemleri mvp_audit tablosuna yazılır."}
                </p>
                <button className="secondary-button" onClick={() => setRailSection("studies")}>Çalışmaya dön</button>
              </div>
            </section>
          ) : (
          <>
          <div className="design-intent">
            <div>
              <span className="context-label">Tasarım niyeti</span>
              <p>
                {activeNode.design_intent}
              </p>
            </div>
          </div>

          <div className="tab-bar" role="tablist" aria-label="Node çalışma alanları">
            {workspaceTabs(rows.length, lopaLayerCount).map((tab) => (
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
                onDeleteRow={removeSelectedRow}
                evidenceOpen={evidenceOpen}
                onToggleEvidence={() => setEvidenceOpen((current) => !current)}
              />
              <div className={`hazop-layout ${evidenceOpen ? "with-evidence" : ""}`}>
                {loadingRows ? (
                  <div className="table-loading">Node satırları yükleniyor...</div>
                ) : rows.length === 0 ? (
                  <div className="table-empty">
                    <Table2 size={28} />
                    <strong>Bu node için HAZOP satırı yok</strong>
                    <p>İlk sapmayı kaydetmek için yeni satır oluşturun.</p>
                    <button className="primary-button" onClick={addRow}><Plus size={16} /> İlk satırı ekle</button>
                  </div>
                ) : <HazopTable
                  rows={rows}
                  selectedRow={selectedRow}
                  onSelectRow={setSelectedRow}
                  onUpdateRow={updateRow}
                />}
                <EvidencePanel
                  open={evidenceOpen}
                  onClose={() => setEvidenceOpen(false)}
                  onApply={applySuggestion}
                  suggestions={workspaceSuggestions}
                />
              </div>
            </>
          )}
          {activeTab === "LOPA" && <LopaWorkspace selectedRow={selected} />}
          {activeTab === "Risk matrisi" && <RiskMatrix />}
          {activeTab === "Kaynaklar" && <SourcesWorkspace />}
          {activeTab === "Ürün durumu" && <ProductStatusWorkspace status={productStatus} />}
          </>
          )}
        </main>

        <footer className="status-bar">
          <div>
            <Activity size={14} />
            <span>{rows.length} satır</span>
            <span className="status-separator" />
            <span>{rows.filter((r) => r.status === "Eksik").length} eksik</span>
            <span className="status-separator" />
            <span className="local-data">
              <ShieldCheck size={14} />
              Veri yerel ortamda
            </span>
          </div>
          <div className="shortcut-hints">
            <span><kbd>Ctrl</kbd><kbd>Enter</kbd> Satır ekle</span>
          </div>
        </footer>
      </div>

      {toast && (
        <div className={`toast toast-${toast.type}`} role={toast.type === "error" ? "alert" : "status"}>
          {toast.type === "error" ? <AlertTriangle size={18} /> : <CheckCircle2 size={18} />}
          {toast.message}
        </div>
      )}
      <CreateStudyDialog
        open={studyDialogOpen}
        onClose={() => setStudyDialogOpen(false)}
        onError={(msg) => notify(msg, "error")}
        onCreated={(created) => {
          setStudyOptions((current) => [created, ...current]);
          setStudy({
            ...created,
            progress: 0,
            reviewed_scenarios: 0,
            total_scenarios: 0,
          });
          setWorkspaceNodes([]);
          setRows([]);
          setStudyDialogOpen(false);
          setNodeDialogOpen(true);
          notify("Çalışma oluşturuldu. Şimdi ilk node'u ekleyin.");
        }}
      />
      <CreateNodeDialog
        open={nodeDialogOpen}
        studyId={study.id}
        onClose={() => setNodeDialogOpen(false)}
        onError={(msg) => notify(msg, "error")}
        onCreated={(created) => {
          setWorkspaceNodes((current) => [...current, created]);
          setActiveNodeId(created.id);
          setRows([]);
          setNodeDialogOpen(false);
          notify("Node oluşturuldu.");
        }}
      />
      <button className="floating-create-study" onClick={() => setStudyDialogOpen(true)}>
        <Plus size={17} /> Yeni çalışma
      </button>
    </div>
  );
}

export default function App() {
  return window.location.pathname.startsWith("/app") ? <WorkspaceApp /> : <LandingPage />;
}
