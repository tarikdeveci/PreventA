import {
  Activity,
  AlertTriangle,
  Archive,
  ArrowUpRight,
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
  Database,
  FileClock,
  FileOutput,
  Files,
  Fingerprint,
  Gauge,
  History,
  LayoutGrid,
  Layers3,
  ListChecks,
  Lock,
  Menu,
  MoreHorizontal,
  PanelRightClose,
  Plus,
  Search,
  ScanLine,
  Settings,
  ShieldCheck,
  Sparkles,
  Table2,
  Trash2,
  X,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  ApiError,
  addLopaLayer,
  createHazopRow,
  createNode,
  createStudy,
  deleteHazopRow,
  deleteLopaLayer,
  fetchDeviationAssist,
  fetchLopaLayers,
  fetchNodes,
  fetchProductStatus,
  fetchRows,
  fetchStudies,
  fetchWorkspace,
  reportUrl,
  updateHazopRow,
  fetchSession,
  logout as logoutSession,
} from "./api";
import { LoginPage } from "@/components/login-page";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  emptyStudy,
  type AuthUser,
  type HazopRow,
  type LopaLayer,
  type ProductStatus,
  type StudyListItem,
  type Suggestion,
  type WorkspaceNode,
  type WorkspaceStudy,
  unavailableStatus,
} from "./data";

type WorkspaceTab = "HAZOP" | "LOPA" | "Risk matrix" | "Sources" | "Product status";

function workspaceTabs(rowCount: number, lopaCount: number): { label: WorkspaceTab; count?: number }[] {
  return [
    { label: "HAZOP", count: rowCount || undefined },
    { label: "LOPA", count: lopaCount || undefined },
    { label: "Risk matrix" },
    { label: "Sources" },
    { label: "Product status" },
  ];
}

function RiskBadge({ level }: { level: HazopRow["risk"] }) {
  const labels = { Düşük: "Low", Orta: "Medium", Yüksek: "High", Kritik: "Critical" };
  return <span className={`risk-badge risk-${level.toLocaleLowerCase("tr")}`}>{labels[level]}</span>;
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
    <aside className="app-rail" aria-label="Main application">
      <button className="brand-mark" aria-label="PreventA home">
        <img src="/brand/preventa-mark.png" alt="" />
      </button>
      <nav className="rail-nav" aria-label="Application sections">
        <button
          className={`rail-button ${active === "studies" ? "is-active" : ""}`}
          aria-label="Studies"
          title="Studies"
          onClick={() => onSelect("studies")}
        >
          <Files size={20} />
        </button>
        <button
          className={`rail-button ${active === "library" ? "is-active" : ""}`}
          aria-label="Scenario library"
          title="Scenario library"
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
          aria-label="Audit history"
          title="Audit history"
          onClick={() => onSelect("history")}
        >
          <History size={20} />
        </button>
      </nav>
      <div className="rail-footer">
        <button className="rail-button" aria-label="Help" title="Help">
          <CircleHelp size={20} />
        </button>
        <button className="rail-button" aria-label="Settings" title="Settings">
          <Settings size={20} />
        </button>
        <button className="avatar-button" aria-label="User account" title="User">
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
  canWrite,
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
  canWrite: boolean;
}) {
  const [query, setQuery] = useState("");
  const filteredNodes = nodes.filter((node) =>
    `${node.code} ${node.name}`.toLocaleLowerCase("tr").includes(query.toLocaleLowerCase("tr")),
  );

  return (
    <>
      {open && <button className="nav-scrim" onClick={onClose} aria-label="Close navigation" />}
      <aside className={`study-nav ${open ? "is-open" : ""}`} aria-label="Study navigation">
        <div className="study-nav-header">
          <div>
            <span className="context-label">Active study</span>
            <strong>{study.title}</strong>
          </div>
          <button className="icon-button mobile-only" onClick={onClose} aria-label="Close navigation">
            <X size={18} />
          </button>
        </div>

        <div className="study-switcher">
          <span className="study-monogram">RA</span>
          <span>
            <label className="sr-only" htmlFor="study-selector">Select active study</label>
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
            <span>Study structure</span>
            <button
              className="compact-icon"
              aria-label="Add node"
              onClick={onCreateNode}
              disabled={!canWrite}
            >
              <Plus size={15} />
            </button>
          </div>
          <button className="nav-row">
            <LayoutGrid size={17} />
            <span>Overview</span>
          </button>
          <button className="nav-row">
            <ClipboardCheck size={17} />
            <span>Study information</span>
          </button>
          <button className="nav-row">
            <Gauge size={17} />
            <span>Risk matrix</span>
            <span className="nav-meta">5 × 5</span>
          </button>
        </div>

        <div className="nav-section nodes-section">
          <div className="nav-section-title">
            <span>Nodes</span>
            <span className="nav-count">{nodes.length}</span>
          </div>
          <label className="node-search">
            <Search size={15} aria-hidden="true" />
            <span className="sr-only">Search nodes</span>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search nodes"
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
            <span>Study progress</span>
            <strong>%{study.progress}</strong>
          </div>
          <div
            className="progress-track"
            aria-label={`Study progress ${study.progress} percent`}
          >
            <span style={{ width: `${study.progress}%` }} />
          </div>
          <small>
            {study.reviewed_scenarios} / {study.total_scenarios} scenarios reviewed
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
  user,
  onLogout,
}: {
  onOpenNav: () => void;
  onExport: () => void;
  activeNode: WorkspaceNode;
  studyTitle: string;
  apiConnected: boolean;
  user: AuthUser;
  onLogout: () => void;
}) {
  const roleLabels = {
    admin: "Administrator",
    facilitator: "Facilitator",
    viewer: "Viewer",
  } as const;
  return (
    <header className="top-bar">
      <div className="top-context">
        <button className="icon-button nav-trigger" onClick={onOpenNav} aria-label="Open study navigation">
          <Menu size={20} />
        </button>
        <div>
          <div className="breadcrumb">
            <span>Studies</span>
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
        <Badge variant={apiConnected ? "secondary" : "outline"} className="api-state">
          <Cloud size={14} />
          {apiConnected ? "API connected" : "API disconnected"}
        </Badge>
        <span className="save-state">
          <Check size={14} />
          All changes saved
        </span>
        <Button variant="outline" size="sm">
          <History size={16} />
          History
        </Button>
        <Button size="sm" onClick={onExport}>
          <Download size={16} />
          Generate report
        </Button>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="user-menu-trigger">
              <Avatar>
                <AvatarFallback>
                  {user.full_name.split(" ").map((part) => part[0]).join("").slice(0, 2)}
                </AvatarFallback>
              </Avatar>
              <span className="user-menu-copy">
                <strong>{user.full_name}</strong>
                <small>{roleLabels[user.role]}</small>
              </span>
              <ChevronDown data-icon="inline-end" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="user-dropdown">
            <DropdownMenuLabel>
              <strong>{user.full_name}</strong>
              <span>{user.email}</span>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuGroup>
              <DropdownMenuItem>
                <ShieldCheck />
                Role: {roleLabels[user.role]}
              </DropdownMenuItem>
              <DropdownMenuItem onClick={onLogout}>
                <X />
                Sign out
              </DropdownMenuItem>
            </DropdownMenuGroup>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}

function WorksheetToolbar({
  onAddRow,
  onDeleteRow,
  evidenceOpen,
  onToggleEvidence,
  suggestionCount,
  canWrite,
  canDelete,
}: {
  onAddRow: () => void;
  onDeleteRow: () => void;
  evidenceOpen: boolean;
  onToggleEvidence: () => void;
  suggestionCount: number;
  canWrite: boolean;
  canDelete: boolean;
}) {
  return (
    <div className="worksheet-toolbar">
      <div className="toolbar-group">
        <button className="secondary-button compact" onClick={onAddRow} disabled={!canWrite}>
          <Plus size={16} />
          Add row
        </button>
        <button
          className="secondary-button compact danger-action"
          onClick={onDeleteRow}
          disabled={!canDelete}
        >
          <Trash2 size={16} />
          Delete row
        </button>
        <button className="secondary-button compact" disabled title="Coming soon">
          <Archive size={16} />
          Add from library
        </button>
        <span className="toolbar-divider" />
        <label className="table-search">
          <Search size={15} />
          <span className="sr-only">Search worksheet</span>
          <input placeholder="Search worksheet" />
        </label>
      </div>
      <div className="toolbar-group">
        <button className="secondary-button compact">
          <Table2 size={16} />
          Columns
        </button>
        <button
          className={`evidence-toggle ${evidenceOpen ? "is-active" : ""}`}
          onClick={onToggleEvidence}
          aria-pressed={evidenceOpen}
        >
          <Sparkles size={16} />
          Grounded suggestions
          <span>{suggestionCount}</span>
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
  readOnly,
}: {
  rows: HazopRow[];
  selectedRow: number;
  onSelectRow: (id: number) => void;
  onUpdateRow: (id: number, field: keyof HazopRow, value: string) => void;
  readOnly: boolean;
}) {
  return (
    <div className="table-frame">
      <table className="hazop-table">
        <thead>
          <tr>
            <th className="row-index">#</th>
            <th className="col-guideword">Guideword</th>
            <th className="col-deviation">Deviation</th>
            <th className="col-text">Cause</th>
            <th className="col-text">Consequence</th>
            <th className="col-text">Existing safeguards</th>
            <th className="col-score">S</th>
            <th className="col-score">O</th>
            <th className="col-risk">Risk</th>
            <th className="col-status">Review</th>
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
                  aria-label={`${index + 1}. select row`}
                  aria-pressed={row.id === selectedRow}
                >
                  {index + 1}
                </button>
              </td>
              <td>
                <select
                  aria-label={`${index + 1}. row guideword`}
                  value={row.guideword}
                  disabled={readOnly}
                  onChange={(event) => onUpdateRow(row.id, "guideword", event.target.value)}
                >
                  <option value="Yok">No</option>
                  <option value="Fazla">More</option>
                  <option value="Az">Less</option>
                  <option value="Ters">Reverse</option>
                  <option value="Başka">Other</option>
                </select>
              </td>
              <td>
                <textarea
                  aria-label={`${index + 1}. row deviation`}
                  value={row.deviation}
                  readOnly={readOnly}
                  onChange={(event) => onUpdateRow(row.id, "deviation", event.target.value)}
                />
              </td>
              <td>
                <textarea
                  aria-label={`${index + 1}. row cause`}
                  value={row.cause}
                  readOnly={readOnly}
                  onChange={(event) => onUpdateRow(row.id, "cause", event.target.value)}
                />
              </td>
              <td>
                <textarea
                  aria-label={`${index + 1}. row consequence`}
                  value={row.consequence}
                  readOnly={readOnly}
                  onChange={(event) => onUpdateRow(row.id, "consequence", event.target.value)}
                />
              </td>
              <td>
                <textarea
                  aria-label={`${index + 1}. row existing safeguards`}
                  value={row.safeguard}
                  readOnly={readOnly}
                  onChange={(event) => onUpdateRow(row.id, "safeguard", event.target.value)}
                />
              </td>
              <td className="score-cell">
                <select
                  aria-label={`${index + 1}. row severity`}
                  value={row.severity}
                  disabled={readOnly}
                  onChange={(event) => onUpdateRow(row.id, "severity", event.target.value)}
                >
                  {[1, 2, 3, 4, 5].map((v) => <option key={v} value={v}>{v}</option>)}
                </select>
              </td>
              <td className="score-cell">
                <select
                  aria-label={`${index + 1}. row likelihood`}
                  value={row.likelihood}
                  disabled={readOnly}
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
                  aria-label={`${index + 1}. row review status`}
                  value={row.status}
                  disabled={readOnly}
                  className={`status-select status-${row.status.toLocaleLowerCase("tr")}`}
                  onChange={(event) => onUpdateRow(row.id, "status", event.target.value)}
                >
                  <option value="Eksik">Incomplete</option>
                  <option value="Taslak">Draft</option>
                  <option value="İncelendi">Reviewed</option>
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
  onRequest,
  selectedRow,
  suggestions,
  state,
  error,
  canRequest,
}: {
  open: boolean;
  onClose: () => void;
  onApply: (suggestionId: string) => void;
  onRequest: () => void;
  selectedRow: HazopRow | undefined;
  suggestions: Suggestion[];
  state: "idle" | "loading" | "ready" | "error";
  error: string | null;
  canRequest: boolean;
}) {
  return (
    <aside className={`evidence-panel ${open ? "is-open" : ""}`} aria-label="Grounded suggestions">
      <div className="evidence-header">
        <div>
          <div className="panel-title">
            <Sparkles size={18} />
            <h2>Grounded suggestions</h2>
          </div>
          <p>Selected row: {selectedRow?.deviation || "No deviation selected"}</p>
        </div>
        <button className="icon-button" onClick={onClose} aria-label="Close suggestion panel">
          <PanelRightClose size={19} />
        </button>
      </div>

      <div className="grounding-note">
        <ShieldCheck size={17} />
        <span>Every candidate is grounded only in accessible study and standards evidence.</span>
      </div>

      <div className="suggestion-list">
        {state === "idle" && (
          <div className="functional-empty">
            <Sparkles size={26} />
            <strong>Generate grounded candidates for the selected deviation</strong>
            <p>The request uses equipment, design intent, guideword and existing safeguards.</p>
            <button
              className="primary-button"
              onClick={onRequest}
              disabled={!selectedRow || !canRequest}
            >
              Generate suggestions
            </button>
          </div>
        )}
        {state === "loading" && (
          <div className="table-loading">Searching sources and validating citations...</div>
        )}
        {state === "error" && (
          <div className="functional-empty">
            <AlertTriangle size={26} />
            <strong>Grounded suggestions could not be generated</strong>
            <p>{error}</p>
            <button className="secondary-button" onClick={onRequest} disabled={!canRequest}>
              Try again
            </button>
          </div>
        )}
        {state === "ready" && suggestions.length === 0 && (
          <div className="functional-empty">
            <ShieldCheck size={26} />
            <strong>Insufficient evidence found</strong>
            <p>Uncited content was withheld. Expand the corpus and try again.</p>
          </div>
        )}
        {suggestions.map((suggestion) => (
          <article className="suggestion-item" key={suggestion.id}>
            <div className="suggestion-meta">
              <span className={`suggestion-kind kind-${suggestion.target}`}>
                {{ Neden: "Cause", Sonuç: "Consequence", Önlem: "Safeguard" }[suggestion.kind]}
              </span>
              <span className="confidence">
                {{ Düşük: "Low", Orta: "Medium", Yüksek: "High" }[suggestion.confidence]} match
              </span>
            </div>
            <p>{suggestion.text}</p>
            {suggestion.citations.map((citation) => (
              <button
                className="citation-button"
                key={citation.chunk_id}
                title={`${citation.source_ref} · ${citation.section_ref ?? "Section not specified"} · ${citation.excerpt}`}
              >
                <FileClock size={14} />
                <span>
                  <strong>{citation.source_ref}</strong>
                  {citation.section_ref ?? "Section not specified"}
                </span>
                <ChevronRight size={14} />
              </button>
            ))}
            <div className="suggestion-actions">
              <button className="text-button">Open source</button>
              <button className="apply-button" onClick={() => onApply(suggestion.id)}>
                <Plus size={15} />
                Add to draft
              </button>
            </div>
          </article>
        ))}
      </div>

      <div className="evidence-footer">
        <Bot size={18} />
        <div>
          <strong>Human review required</strong>
          <p>Suggestions are reviewable drafts, not engineering decisions.</p>
        </div>
      </div>
    </aside>
  );
}

function LopaWorkspace({
  selectedRow,
  readOnly,
}: {
  selectedRow: HazopRow | undefined;
  readOnly: boolean;
}) {
  const [layers, setLayers] = useState<LopaLayer[]>([]);
  const [loading, setLoading] = useState(false);
  const [addOpen, setAddOpen] = useState(false);
  const [form, setForm] = useState({ description: "", pfd: "1.0e-2", is_valid: true, note: "" });
  const selectedRowId = selectedRow?.id;

  useEffect(() => {
    if (!selectedRowId) {
      setLayers([]);
      return;
    }
    setLoading(true);
    fetchLopaLayers(selectedRowId)
      .then(setLayers)
      .catch(() => setLayers([]))
      .finally(() => setLoading(false));
  }, [selectedRowId]);

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
    if (!window.confirm("Delete this IPL record?")) return;
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
          <span>Initiating event frequency</span>
          <strong className="mono">{initiatorFreq.toExponential(1)} /year</strong>
        </div>
        <ChevronRight size={18} />
        <div>
          <span>Total risk reduction</span>
          <strong className="mono">{totalReduction.toExponential(1)}</strong>
        </div>
        <ChevronRight size={18} />
        <div>
          <span>Outcome frequency</span>
          <strong className="mono">{outcomeFreq.toExponential(1)} /year</strong>
        </div>
        <div className="sil-result">
          <span>Selected scenario</span>
          <strong>{selectedRow ? `Row ${selectedRow.id}` : "—"}</strong>
        </div>
      </div>
      <div className="section-heading">
        <div>
          <h2>Independent protection layers</h2>
          <p>
            {selectedRow
              ? `Scenario: ${selectedRow.deviation || "Define the deviation"}`
              : "Select a row from the HAZOP tab."}
          </p>
        </div>
        <button
          className="secondary-button"
          onClick={() => setAddOpen(true)}
          disabled={!selectedRow || readOnly}
        >
          <Plus size={16} />
          Add IPL
        </button>
      </div>

      {loading ? (
        <div className="table-loading">Loading IPL layers...</div>
      ) : layers.length === 0 ? (
        <div className="table-empty">
          <CheckCircle2 size={28} />
          <strong>No IPL records exist for this scenario</strong>
          <p>Use Add IPL to register a protection layer.</p>
        </div>
      ) : (
        <div className="ipl-table">
          <div className="ipl-header">
            <span>Protection layer</span>
            <span>Typical PFD</span>
            <span>IPL validity</span>
            <span>Assessment</span>
            <span />
          </div>
          {layers.map((layer) => (
            <div className="ipl-row" key={layer.id}>
              <strong>{layer.description}</strong>
              <span className="mono">{layer.pfd.toExponential(1)}</span>
              <span className={layer.is_valid ? "ipl-valid" : "ipl-invalid"}>
                {layer.is_valid ? <CheckCircle2 size={15} /> : <AlertTriangle size={15} />}
                {layer.is_valid ? "Valid" : "No credit"}
              </span>
              <p>{layer.note}</p>
              <button
                className="icon-button"
                aria-label="Delete IPL"
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
              <div><h2>Add IPL</h2><p>Enter the independent protection layer details.</p></div>
              <button type="button" className="icon-button" onClick={() => setAddOpen(false)} aria-label="Close"><X size={18} /></button>
            </div>
            <label>Description<input required value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></label>
            <label>PFD (e.g. 1e-2)<input required value={form.pfd} onChange={(e) => setForm({ ...form, pfd: e.target.value })} /></label>
            <label>
              <input type="checkbox" checked={form.is_valid} onChange={(e) => setForm({ ...form, is_valid: e.target.checked })} />
              {" "}Meets IPL validity criteria
            </label>
            <label>Note<textarea value={form.note} onChange={(e) => setForm({ ...form, note: e.target.value })} /></label>
            <div className="dialog-actions">
              <button type="button" className="secondary-button" onClick={() => setAddOpen(false)}>Cancel</button>
              <button className="primary-button">Save</button>
            </div>
          </form>
        </div>
      )}
    </section>
  );
}
function RiskMatrix() {
  const riskZone = { low: "Low", medium: "Medium", high: "High", critical: "Critical" } as const;
  return (
    <section className="matrix-workspace">
      <div className="section-heading">
        <div>
          <h2>Client risk matrix</h2>
          <p>ACWA Power 5 × 5 matrix · Revision 3 · May 12, 2026</p>
        </div>
        <button className="secondary-button">Edit matrix</button>
      </div>
      <div className="matrix-layout">
        <div className="matrix-y-label">Likelihood</div>
        <div className="matrix-grid" role="grid" aria-label="5 by 5 risk matrix">
          {[5, 4, 3, 2, 1].map((likelihood) =>
            [1, 2, 3, 4, 5].map((severity) => {
              const score = likelihood * severity;
              const level = score >= 12 ? "critical" : score >= 8 ? "high" : score >= 4 ? "medium" : "low";
              const zone = riskZone[level];
              return (
                <button
                  key={`${likelihood}-${severity}`}
                  className={`matrix-cell matrix-${level}`}
                  aria-label={`Likelihood ${likelihood}, severity ${severity}, score ${score}, risk ${zone}`}
                >
                  <strong>{score}</strong>
                  <span>{zone}</span>
                </button>
              );
            }),
          )}
        </div>
        <div className="matrix-x-label">Severity</div>
      </div>
    </section>
  );
}

function SourcesWorkspace() {
  return (
    <section className="sources-workspace">
      <div className="section-heading">
        <div>
          <h2>Study sources</h2>
          <p>The controlled knowledge base available to the suggestion engine for this study.</p>
        </div>
        <button className="secondary-button">
          <Plus size={16} />
          Add source
        </button>
      </div>
      <div className="source-list">
        {[
          ["IEC 61882:2016", "Standard", "42 sections", "Jun 12, 2026"],
          ["IEC 61511-1:2016", "Standard", "67 sections", "Jun 12, 2026"],
          ["HAZOP-2024-018 · Amine Unit", "Historical study", "238 scenarios", "Jun 08, 2026"],
          ["HAZOP-2023-041 · Tank Farm", "Historical study", "184 scenarios", "Jun 08, 2026"],
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
            <span>Indexed · {date}</span>
            <button className="icon-button" aria-label={`${title} actions`}>
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
    complete: "Complete",
    in_progress: "In progress",
    planned: "Planned",
  } as const;

  return (
    <section className="delivery-workspace">
      <div className="delivery-hero">
        <div className="delivery-summary">
          <span className="context-label">{status.release}</span>
          <h2>{status.stage}</h2>
          <p>
            The interface is connected to the live API. Persistent PostgreSQL CRUD,
            a live Ollama corpus and report generation are required before pilot use.
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
              {status.api_connected ? "Connected" : "Disconnected"}
            </dd>
          </div>
          <div>
            <dt>Data persistence</dt>
            <dd className={status.persistence === "postgresql" ? "fact-ok" : "fact-warn"}>
              {status.persistence === "postgresql"
                ? "PostgreSQL"
                : status.persistence === "volatile_sqlite"
                  ? "Temporary SQLite"
                  : "API seed"}
            </dd>
          </div>
          <div>
            <dt>AI runtime</dt>
            <dd className={status.ai_runtime === "ollama_connected" ? "fact-ok" : "fact-warn"}>
              {status.ai_runtime === "ollama_connected" ? "Ollama connected" : "Contract ready"}
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
          <h2>Module delivery status</h2>
          <p>Current engineering progress against PRD acceptance criteria.</p>
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
          <strong>Next material milestone</strong>
          <p>
            Connect study, node and worksheet create/update endpoints to PostgreSQL,
            then record the first real pilot study through the same workflow.
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
          <img src="/brand/preventa-logo.png" alt="PreventA — Intelligence for HAZOP" />
        </a>
        <nav aria-label="Primary navigation">
          <a href="#platform">Platform</a>
          <a href="#assurance">Assurance</a>
          <a href="#workflow">Workflow</a>
        </nav>
        <a className="landing-login" href="/app">
          Enter workspace <ArrowUpRight size={15} />
        </a>
      </header>

      <main>
        <section className="landing-hero">
          <div className="hero-copy">
            <div className="hero-kicker">
              <span className="signal-dot" />
              Process intelligence for high-consequence operations
            </div>
            <h1>
              Make every hazard study
              <span> compound into intelligence.</span>
            </h1>
            <p>
              PreventA is the operating layer for HAZOP and LOPA teams: structured
              facilitation, evidence-grounded assistance, controlled decisions and
              audit-ready deliverables in one system.
            </p>
            <div className="hero-actions">
              <a className="hero-primary" href="/app">
                Launch workspace
                <ArrowUpRight size={18} />
              </a>
              <a className="hero-secondary" href="#platform">
                Explore the platform
              </a>
            </div>
            <div className="hero-trust">
              <span><Lock size={15} /> Role-controlled</span>
              <span><Database size={15} /> Deploy on your terms</span>
              <span><Fingerprint size={15} /> Every decision traceable</span>
            </div>
          </div>

          <div className="hero-stage" aria-label="PreventA product intelligence preview">
            <div className="hero-orbit orbit-one" />
            <div className="hero-orbit orbit-two" />
            <div className="hero-system-card">
              <div className="system-card-head">
                <div>
                  <span className="eyebrow">LIVE STUDY / UNIT 200</span>
                  <strong>Feed Pump P-101</strong>
                </div>
                <span className="system-status"><i /> Synced</span>
              </div>
              <div className="system-metrics">
                <div><span>Scenarios</span><strong>24</strong><small>+4 this session</small></div>
                <div><span>Critical</span><strong className="metric-alert">03</strong><small>Review required</small></div>
                <div><span>Coverage</span><strong>87%</strong><small>Evidence mapped</small></div>
              </div>
              <div className="system-grid">
                <div className="risk-radar">
                  <span className="radar-label">RISK SIGNAL</span>
                  <div className="radar-core"><ScanLine /><strong>12</strong><small>risk score</small></div>
                  <span className="radar-node node-a" />
                  <span className="radar-node node-b" />
                  <span className="radar-node node-c" />
                </div>
                <div className="scenario-stream">
                  <div className="stream-head"><span>Deviation stream</span><small>4 active</small></div>
                  {[
                    ["NO FLOW", "Isolation valve closed", "MEDIUM"],
                    ["MORE FLOW", "FV-101 failed open", "HIGH"],
                    ["REVERSE FLOW", "Check valve leakage", "CRITICAL"],
                  ].map(([deviation, cause, risk]) => (
                    <div className="stream-row" key={deviation}>
                      <span className={`stream-signal signal-${risk.toLowerCase()}`} />
                      <div><strong>{deviation}</strong><small>{cause}</small></div>
                      <em>{risk}</em>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <div className="floating-card evidence-float">
              <span><Sparkles size={14} /> EVIDENCE ENGINE</span>
              <strong>3 grounded safeguards found</strong>
              <div className="evidence-line"><i /><span>IEC 61882 §6.3</span><b>98%</b></div>
              <div className="evidence-line"><i /><span>HAZOP-2024-018</span><b>91%</b></div>
            </div>
            <div className="floating-card control-float">
              <ShieldCheck size={18} />
              <div><strong>Human approval gate</strong><span>AI cannot commit decisions</span></div>
            </div>
            <div className="hero-index">
              <span>01</span>
              <div />
              <span>CONTROLLED INTELLIGENCE</span>
            </div>
          </div>
        </section>

        <section className="signal-strip">
          <span>BUILT FOR</span>
          <div>Process safety teams</div>
          <div>Engineering consultancies</div>
          <div>Asset operators</div>
          <div>Regulated facilities</div>
        </section>

        <section className="landing-section platform-section" id="platform">
          <div className="section-number">02 / PLATFORM</div>
          <div className="landing-section-heading">
            <h2>One operational surface.<br />No fragmented decisions.</h2>
            <p>
              Facilitation, risk evaluation, protection layers, evidence and reporting
              stay connected to the same scenario context.
            </p>
          </div>
          <div className="capability-grid">
            {[
              [Layers3, "Structured studies", "Run keyboard-first HAZOP sessions with a model that preserves study, node and scenario context."],
              [Sparkles, "Grounded assistance", "Retrieve candidate causes and safeguards only when accessible evidence can be cited."],
              [ShieldCheck, "Decision controls", "Separate machine suggestions from approved engineering decisions with explicit review gates."],
              [FileOutput, "Audit-ready output", "Generate editable deliverables while retaining source, role and change history."],
            ].map(([Icon, title, detail], index) => {
              const CapabilityIcon = Icon as typeof Layers3;
              return (
                <article key={title as string}>
                  <div className="capability-top"><span>0{index + 1}</span><CapabilityIcon size={22} /></div>
                  <h3>{title as string}</h3>
                  <p>{detail as string}</p>
                  <ArrowUpRight size={17} className="capability-arrow" />
                </article>
              );
            })}
          </div>
        </section>

        <section className="assurance-section" id="assurance">
          <div className="assurance-visual">
            <div className="assurance-ring ring-outer" />
            <div className="assurance-ring ring-inner" />
            <div className="assurance-core"><Fingerprint /><strong>CONTROL</strong><span>BY DESIGN</span></div>
            <span className="assurance-tag tag-one">RBAC</span>
            <span className="assurance-tag tag-two">AUDIT LOG</span>
            <span className="assurance-tag tag-three">ON-PREM READY</span>
          </div>
          <div className="assurance-copy">
            <span className="section-number">03 / ASSURANCE</span>
            <h2>Your engineering data stays governed.</h2>
            <p>
              PreventA keeps retrieval, generation and approval as explicit system
              boundaries. Deploy the data and model layers in your environment, control
              capabilities by role, and retain a trace for every material change.
            </p>
            <div className="assurance-list">
              <span><CheckCircle2 /> Opaque, expiring sessions</span>
              <span><CheckCircle2 /> Administrator, facilitator and viewer roles</span>
              <span><CheckCircle2 /> Evidence required before AI output is shown</span>
            </div>
          </div>
        </section>

        <section className="workflow-section" id="workflow">
          <div className="section-number">04 / WORKFLOW</div>
          <div className="workflow-heading">
            <h2>From design intent<br />to defensible report.</h2>
            <a href="/app">Start a study <ArrowUpRight size={16} /></a>
          </div>
          <ol>
            {[
              ["Frame", "Capture the facility, system boundaries and risk context."],
              ["Explore", "Run HAZOP and LOPA with structured scenarios and protection layers."],
              ["Challenge", "Review grounded candidates and preserve engineering ownership."],
              ["Deliver", "Export an editable report with its decision trail intact."],
            ].map(([title, detail], index) => (
              <li key={title}>
                <span>0{index + 1}</span>
                <div><strong>{title}</strong><p>{detail}</p></div>
              </li>
            ))}
          </ol>
        </section>

        <section className="landing-closing">
          <span className="section-number">READY WHEN THE ROOM IS</span>
          <h2>Turn the next study into institutional memory.</h2>
          <a href="/app">Enter PreventA <ArrowUpRight size={20} /></a>
          <div className="closing-grid" aria-hidden="true">
            {Array.from({ length: 36 }).map((_, index) => <span key={index} />)}
          </div>
        </section>
      </main>
      <footer className="landing-footer">
        <span>PreventA / Process Safety Intelligence</span>
        <span>Built for controlled engineering decisions</span>
        <span>© 2026</span>
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
            onError("The study could not be created. Check the API connection.");
          } finally {
            setSaving(false);
          }
        }}
      >
        <div className="dialog-heading">
          <div><h2>New study</h2><p>Define the client and facility context.</p></div>
          <button type="button" className="icon-button" onClick={onClose} aria-label="Close"><X size={18} /></button>
        </div>
        <label>Study name<input required value={values.title} onChange={(e) => setValues({...values, title: e.target.value})} /></label>
        <label>Client<input required value={values.client} onChange={(e) => setValues({...values, client: e.target.value})} /></label>
        <label>Facility<input required value={values.facility} onChange={(e) => setValues({...values, facility: e.target.value})} /></label>
        <div className="dialog-actions">
          <button type="button" className="secondary-button" onClick={onClose}>Cancel</button>
          <button className="primary-button" disabled={saving}>{saving ? "Creating" : "Create study"}</button>
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
            onError("The node could not be created. Check the API connection.");
          } finally {
            setSaving(false);
          }
        }}
      >
        <div className="dialog-heading">
          <div><h2>New node</h2><p>Use a precise equipment type to improve suggestion quality.</p></div>
          <button type="button" className="icon-button" onClick={onClose} aria-label="Close"><X size={18} /></button>
        </div>
        <label>Node code<input required placeholder="N-06" value={values.code} onChange={(e) => setValues({...values, code: e.target.value})} /></label>
        <label>Node name<input required value={values.name} onChange={(e) => setValues({...values, name: e.target.value})} /></label>
        <label>Equipment type<input required value={values.equipment_type} onChange={(e) => setValues({...values, equipment_type: e.target.value})} /></label>
        <label>Design intent<textarea required value={values.design_intent} onChange={(e) => setValues({...values, design_intent: e.target.value})} /></label>
        <div className="dialog-actions">
          <button type="button" className="secondary-button" onClick={onClose}>Cancel</button>
          <button className="primary-button" disabled={saving}>{saving ? "Creating" : "Create node"}</button>
        </div>
      </form>
    </div>
  );
}

function WorkspaceApp({
  user,
  onLogout,
}: {
  user: AuthUser;
  onLogout: () => void;
}) {
  const [activeTab, setActiveTab] = useState<WorkspaceTab>("HAZOP");
  const [railSection, setRailSection] = useState<RailSection>("studies");
  const [rows, setRows] = useState<HazopRow[]>([]);
  const lopaLayerCount = 0;
  const [workspaceNodes, setWorkspaceNodes] = useState<WorkspaceNode[]>([]);
  const [study, setStudy] = useState(emptyStudy);
  const [studyOptions, setStudyOptions] = useState<StudyListItem[]>([]);
  const [workspaceSuggestions, setWorkspaceSuggestions] = useState<Suggestion[]>([]);
  const [evidenceState, setEvidenceState] =
    useState<"idle" | "loading" | "ready" | "error">("idle");
  const [evidenceError, setEvidenceError] = useState<string | null>(null);
  const [productStatus, setProductStatus] = useState(unavailableStatus);
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
  const canWrite = user.permissions.includes("workspace:write");
  const canDelete = user.permissions.includes("workspace:delete");
  const canUseRag = user.permissions.includes("rag:use");

  const selected = useMemo(
    () => rows.find((row) => row.id === selectedRow) ?? rows[0],
    [rows, selectedRow],
  );

  useEffect(() => {
    setWorkspaceSuggestions([]);
    setEvidenceState("idle");
    setEvidenceError(null);
  }, [activeNodeId, selectedRow]);
  const activeNode = useMemo(
    () =>
      workspaceNodes.find((node) => node.id === activeNodeId) ??
      workspaceNodes[0] ??
      {
        id: "",
        code: "",
        name: "No node selected",
        equipment_type: "Waiting for study",
        design_intent: "Select a study and node to begin.",
        scenario_count: 0,
        state: "empty" as const,
      },
    [activeNodeId, workspaceNodes],
  );

  useEffect(() => {
    let active = true;
    Promise.all([fetchProductStatus(), fetchStudies(), fetchWorkspace()])
      .then(([status, studies, workspace]) => {
        if (!active) return;
        setProductStatus(status);
        setApiConnected(status.api_connected);
        setStudyOptions(studies);
        setStudy(workspace.study);
        setWorkspaceNodes(workspace.nodes);
        setActiveNodeId(workspace.active_node_id);
        setRows(workspace.rows);
        setSelectedRow(workspace.rows[0]?.id ?? 0);
      })
      .catch(() => {
        if (!active) return;
        setApiConnected(false);
        setProductStatus(unavailableStatus);
      });
    return () => {
      active = false;
    };
  }, []);

  // Keyboard shortcut: Ctrl+Enter to add row
  const addRowRef = useRef<(() => Promise<void>) | undefined>(undefined);
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
        notify("The change remains in the local draft. Check the API connection.", "error");
      }
    }, 550);
  };

  const addRow = async () => {
    if (!activeNodeId) {
      notify("Create a node before adding a row.", "error");
      return;
    }
    try {
      const created = await createHazopRow(activeNodeId);
      setRows((current) => [...current, created]);
      setSelectedRow(created.id);
      notify("A new HAZOP row was added.");
    } catch {
      notify("The row could not be created. Check the API connection.", "error");
    }
  };

  // Keep ref in sync so keyboard handler can call latest addRow
  useEffect(() => { addRowRef.current = addRow; });

  const removeSelectedRow = async () => {
    if (!selected) return;
    if (!window.confirm("Permanently delete the selected HAZOP row?")) return;
    try {
      await deleteHazopRow(selected.id);
      const remaining = rows.filter((row) => row.id !== selected.id);
      setRows(remaining);
      setSelectedRow(remaining[0]?.id ?? 0);
      notify("HAZOP row deleted.");
    } catch {
      notify("The row could not be deleted.", "error");
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
      notify("The study could not be loaded. Check the API connection.", "error");
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
    const kind = { Neden: "Cause", Sonuç: "Consequence", Önlem: "Safeguard" }[suggestion.kind];
    notify(`${kind} suggestion added to row ${selected.id}.`);
  };

  const requestSuggestions = async () => {
    if (!selected || !activeNode.id) {
      setEvidenceState("error");
      setEvidenceError("Select a node and HAZOP row before generating suggestions.");
      return;
    }

    setEvidenceState("loading");
    setEvidenceError(null);
    try {
      const response = await fetchDeviationAssist({
        study_id: study.id,
        node_id: activeNode.id,
        equipment_type: activeNode.equipment_type,
        design_intent: activeNode.design_intent,
        parameter: selected.deviation.trim() || selected.guideword,
        guideword: selected.guideword,
        deviation: selected.deviation.trim() || `${selected.guideword} deviation`,
        existing_safeguards: selected.safeguard.trim() ? [selected.safeguard.trim()] : [],
      });
      const kindLabel = {
        cause: "Neden",
        consequence: "Sonuç",
        safeguard: "Önlem",
      } as const;
      const confidenceLabel = {
        low: "Düşük",
        medium: "Orta",
        high: "Yüksek",
      } as const;
      setWorkspaceSuggestions(
        response.candidates.map((candidate, index) => ({
          id: `${response.suggestion_id}-${index}`,
          kind: kindLabel[candidate.kind],
          text: candidate.text,
          confidence: confidenceLabel[candidate.confidence],
          citations: candidate.citations,
          target: candidate.kind,
        })),
      );
      setEvidenceState("ready");
      setApiConnected(true);
    } catch (error) {
      setWorkspaceSuggestions([]);
      setEvidenceState("error");
      setEvidenceError(
        error instanceof ApiError && error.code === "ungrounded_suggestion"
          ? "The model could not produce sufficient verifiable citations, so the safety rule blocked the response."
          : "The RAG service is unavailable. Check PostgreSQL, corpus and Ollama connectivity.",
      );
    }
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
        canWrite={canWrite}
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
          user={user}
          onLogout={onLogout}
        />

        <main id="main-content" className="main-workspace">
          {railSection !== "studies" ? (
            <section className="rail-section-page">
              <div className="section-heading">
                <div>
                  <h2>
                    {railSection === "library"
                      ? "Scenario library"
                      : railSection === "reports"
                        ? "Reports"
                        : "Audit history"}
                  </h2>
                  <p>
                    {railSection === "library"
                      ? "Manage approved cause, consequence and safeguard records by equipment type."
                      : railSection === "reports"
                        ? "Download DOCX reports generated from studies."
                        : "Audit trail for study, node and worksheet changes."}
                  </p>
                </div>
                {railSection === "reports" && (
                  <button className="primary-button" onClick={() => { window.location.href = reportUrl(study.id, activeNode.id); }}>
                    <Download size={16} /> Download active node report
                  </button>
                )}
              </div>
              <div className="functional-empty">
                {railSection === "library" ? <BookOpen size={28} /> : railSection === "reports" ? <FileOutput size={28} /> : <History size={28} />}
                <strong>{railSection === "history" ? "Audit records are retained by the backend" : "This module is connected to the MVP workflow"}</strong>
                <p>
                  {railSection === "library"
                    ? `${workspaceSuggestions.length} grounded suggestions are available in the active study context.`
                    : railSection === "reports"
                      ? "The report action generates an editable DOCX through the live API."
                      : "Create, update and delete actions are recorded in the mvp_audit table."}
                </p>
                <button className="secondary-button" onClick={() => setRailSection("studies")}>Return to study</button>
              </div>
            </section>
          ) : (
          <>
          <div className="design-intent">
            <div>
              <span className="context-label">Design intent</span>
              <p>
                {activeNode.design_intent}
              </p>
            </div>
          </div>

          <div className="tab-bar" role="tablist" aria-label="Node workspaces">
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
                suggestionCount={workspaceSuggestions.length}
                canWrite={canWrite}
                canDelete={canDelete}
              />
              <div className={`hazop-layout ${evidenceOpen ? "with-evidence" : ""}`}>
                {loadingRows ? (
                  <div className="table-loading">Loading node rows...</div>
                ) : rows.length === 0 ? (
                  <div className="table-empty">
                    <Table2 size={28} />
                    <strong>No HAZOP rows exist for this node</strong>
                    <p>Create the first row to capture a deviation.</p>
                    <button className="primary-button" onClick={addRow}><Plus size={16} /> Add first row</button>
                  </div>
                ) : <HazopTable
                  rows={rows}
                  selectedRow={selectedRow}
                  onSelectRow={setSelectedRow}
                  onUpdateRow={updateRow}
                  readOnly={!canWrite}
                />}
                <EvidencePanel
                  open={evidenceOpen}
                  onClose={() => setEvidenceOpen(false)}
                  onApply={applySuggestion}
                  onRequest={requestSuggestions}
                  selectedRow={selected}
                  suggestions={workspaceSuggestions}
                  state={evidenceState}
                  error={evidenceError}
                  canRequest={canUseRag}
                />
              </div>
            </>
          )}
          {activeTab === "LOPA" && (
            <LopaWorkspace selectedRow={selected} readOnly={!canWrite} />
          )}
          {activeTab === "Risk matrix" && <RiskMatrix />}
          {activeTab === "Sources" && <SourcesWorkspace />}
          {activeTab === "Product status" && <ProductStatusWorkspace status={productStatus} />}
          </>
          )}
        </main>

        <footer className="status-bar">
          <div>
            <Activity size={14} />
            <span>{rows.length} rows</span>
            <span className="status-separator" />
            <span>{rows.filter((r) => r.status === "Eksik").length} incomplete</span>
            <span className="status-separator" />
            <span className="local-data">
              <ShieldCheck size={14} />
              Data stored locally
            </span>
          </div>
          <div className="shortcut-hints">
            <span><kbd>Ctrl</kbd><kbd>Enter</kbd> Add row</span>
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
          notify("Study created. Add the first node.");
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
          notify("Create nodeuldu.");
        }}
      />
      {canWrite && (
        <button className="floating-create-study" onClick={() => setStudyDialogOpen(true)}>
          <Plus size={17} /> New study
        </button>
      )}
    </div>
  );
}

export default function App() {
  const appRoute = window.location.pathname.startsWith("/app");
  const [user, setUser] = useState<AuthUser | null>(null);
  const [authLoading, setAuthLoading] = useState(appRoute);

  useEffect(() => {
    if (!appRoute) return;
    fetchSession()
      .then((session) => setUser(session.user))
      .catch(() => setUser(null))
      .finally(() => setAuthLoading(false));
  }, [appRoute]);

  if (!appRoute) return <LandingPage />;
  if (authLoading) {
    return (
      <main className="auth-loading">
        <ShieldCheck />
        <strong>Preparing PreventA</strong>
        <span>Verifying secure session...</span>
      </main>
    );
  }
  if (!user) return <LoginPage onLogin={setUser} />;

  return (
    <WorkspaceApp
      user={user}
      onLogout={async () => {
        setUser(null);
        try {
          await logoutSession();
        } catch {
          // The local session is closed even if the server is temporarily unreachable.
        }
      }}
    />
  );
}
