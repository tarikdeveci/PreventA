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
  PanelRightClose,
  Plus,
  Search,
  ScanLine,
  Settings,
  ShieldCheck,
  Sparkles,
  Table2,
  Trash2,
  Upload,
  X,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ApiError,
  addLopaLayer,
  createHazopRow,
  createNode,
  createStudy,
  importOphaStudy,
  deleteHazopRow,
  deleteLopaLayer,
  fetchDeviationEvidence,
  fetchLopaLayers,
  fetchNodes,
  fetchProductStatus,
  fetchRows,
  fetchStudies,
  fetchWorkspace,
  reportUrl,
  updateHazopRow,
  fetchSession,
  fetchLibrary,
  createLibraryEntry,
  deleteLibraryEntry,
  fetchSources,
  createSource,
  updateSource,
  deleteSource,
  fetchRiskMatrix,
  updateRiskMatrix,
  fetchAudit,
  fetchReports,
  fetchUsers,
  createUser,
  updateStudy,
  logout as logoutSession,
} from "./api";
import type { OphaImportResult } from "./api";
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
  type LibraryEntry,
  type StudySource,
  type RiskMatrixSettings,
  type AuditEntry,
  type ReportEntry,
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
  onHelp,
  onSettings,
  user,
}: {
  active: RailSection;
  onSelect: (section: RailSection) => void;
  onHelp: () => void;
  onSettings: () => void;
  user: AuthUser;
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
        <button className="rail-button" aria-label="Help" title="Help" onClick={onHelp}>
          <CircleHelp size={20} />
        </button>
        <button className="rail-button" aria-label="Settings" title="Settings" onClick={onSettings}>
          <Settings size={20} />
        </button>
        <button className="avatar-button" aria-label="User account" title={user.full_name} onClick={onSettings}>
          {user.full_name.slice(0, 1).toUpperCase()}
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
  onOverview,
  onStudyInformation,
  onRiskMatrix,
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
  onOverview: () => void;
  onStudyInformation: () => void;
  onRiskMatrix: () => void;
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
          <button className="nav-row" onClick={onOverview}>
            <LayoutGrid size={17} />
            <span>Overview</span>
          </button>
          <button className="nav-row" onClick={onStudyInformation}>
            <ClipboardCheck size={17} />
            <span>Study information</span>
          </button>
          <button className="nav-row" onClick={onRiskMatrix}>
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
  onHistory,
}: {
  onOpenNav: () => void;
  onExport: () => void;
  activeNode: WorkspaceNode;
  studyTitle: string;
  apiConnected: boolean;
  user: AuthUser;
  onLogout: () => void;
  onHistory: () => void;
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
        <Button variant="outline" size="sm" onClick={onHistory}>
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
  query,
  onQueryChange,
  onOpenLibrary,
  hiddenColumns,
  onToggleColumn,
}: {
  onAddRow: () => void;
  onDeleteRow: () => void;
  evidenceOpen: boolean;
  onToggleEvidence: () => void;
  suggestionCount: number;
  canWrite: boolean;
  canDelete: boolean;
  query: string;
  onQueryChange: (value: string) => void;
  onOpenLibrary: () => void;
  hiddenColumns: Set<string>;
  onToggleColumn: (column: string) => void;
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
        <button className="secondary-button compact" onClick={onOpenLibrary} disabled={!canWrite}>
          <Archive size={16} />
          Add from library
        </button>
        <span className="toolbar-divider" />
        <label className="table-search">
          <Search size={15} />
          <span className="sr-only">Search worksheet</span>
          <input
            placeholder="Search worksheet"
            value={query}
            onChange={(event) => onQueryChange(event.target.value)}
          />
        </label>
      </div>
      <div className="toolbar-group">
        <details className="column-picker">
          <summary className="secondary-button compact">
            <Table2 size={16} />
            Columns
          </summary>
          <div className="column-picker-menu">
            {["cause", "consequence", "safeguard", "scores", "status"].map((column) => (
              <label key={column}>
                <input
                  type="checkbox"
                  checked={!hiddenColumns.has(column)}
                  onChange={() => onToggleColumn(column)}
                />
                {column === "scores" ? "Risk scores" : column[0].toUpperCase() + column.slice(1)}
              </label>
            ))}
          </div>
        </details>
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

// Group worksheet rows by their cause, preserving first-appearance order, so the
// grid can render the Cause -> Consequence hierarchy (review item 7a): each cause
// appears once with its consequence rows beneath it, instead of being repeated.
function groupRowsByCause(rows: HazopRow[]): { key: string; rows: HazopRow[] }[] {
  const groups: { key: string; rows: HazopRow[] }[] = [];
  const indexByKey = new Map<string, number>();
  for (const row of rows) {
    const key = row.cause.trim() ? `cause:${row.cause.trim()}` : `row:${row.id}`;
    const existing = indexByKey.get(key);
    if (existing === undefined) {
      indexByKey.set(key, groups.length);
      groups.push({ key, rows: [row] });
    } else {
      groups[existing].rows.push(row);
    }
  }
  return groups;
}

function HazopConsequenceCells({
  row,
  displayIndex,
  readOnly,
  hiddenColumns,
  onUpdateRow,
}: {
  row: HazopRow;
  displayIndex: number;
  readOnly: boolean;
  hiddenColumns: Set<string>;
  onUpdateRow: (id: number, field: keyof HazopRow, value: string) => void;
}) {
  // The cells to the right of the (grouped) Cause column — one set per consequence.
  return (
    <>
      {!hiddenColumns.has("consequence") && <td>
        <textarea
          aria-label={`${displayIndex}. row consequence`}
          value={row.consequence}
          readOnly={readOnly}
          onChange={(event) => onUpdateRow(row.id, "consequence", event.target.value)}
        />
      </td>}
      {!hiddenColumns.has("safeguard") && <td>
        <textarea
          aria-label={`${displayIndex}. row existing safeguards`}
          value={row.safeguard}
          readOnly={readOnly}
          onChange={(event) => onUpdateRow(row.id, "safeguard", event.target.value)}
        />
      </td>}
      {!hiddenColumns.has("scores") && <><td className="score-cell">
        <select
          aria-label={`${displayIndex}. row severity`}
          value={row.severity}
          disabled={readOnly}
          onChange={(event) => onUpdateRow(row.id, "severity", event.target.value)}
        >
          {[1, 2, 3, 4, 5].map((v) => <option key={v} value={v}>{v}</option>)}
        </select>
      </td>
      <td className="score-cell">
        <select
          aria-label={`${displayIndex}. row likelihood`}
          value={row.likelihood}
          disabled={readOnly}
          onChange={(event) => onUpdateRow(row.id, "likelihood", event.target.value)}
        >
          {[1, 2, 3, 4, 5].map((v) => <option key={v} value={v}>{v}</option>)}
        </select>
      </td>
      <td>
        <RiskBadge level={row.risk} />
      </td></>}
      {!hiddenColumns.has("status") && <td>
        <select
          aria-label={`${displayIndex}. row review status`}
          value={row.status}
          disabled={readOnly}
          className={`status-select status-${row.status.toLocaleLowerCase("tr")}`}
          onChange={(event) => onUpdateRow(row.id, "status", event.target.value)}
        >
          <option value="Eksik">Incomplete</option>
          <option value="Taslak">Draft</option>
          <option value="İncelendi">Reviewed</option>
        </select>
      </td>}
    </>
  );
}

function HazopTable({
  rows,
  selectedRow,
  onSelectRow,
  onUpdateRow,
  onAddConsequence,
  readOnly,
  hiddenColumns,
}: {
  rows: HazopRow[];
  selectedRow: number;
  onSelectRow: (id: number) => void;
  onUpdateRow: (id: number, field: keyof HazopRow, value: string) => void;
  onAddConsequence: (fromRow: HazopRow) => void;
  readOnly: boolean;
  hiddenColumns: Set<string>;
}) {
  const showCause = !hiddenColumns.has("cause");
  const groups = showCause ? groupRowsByCause(rows) : [{ key: "flat", rows }];
  let counter = 0;
  return (
    <div className="table-frame">
      <table className="hazop-table">
        <thead>
          <tr>
            <th className="row-index">#</th>
            <th className="col-guideword">Guideword</th>
            <th className="col-deviation">Deviation</th>
            {showCause && <th className="col-text">Cause</th>}
            {!hiddenColumns.has("consequence") && <th className="col-text">Consequence</th>}
            {!hiddenColumns.has("safeguard") && <th className="col-text">Existing safeguards</th>}
            {!hiddenColumns.has("scores") && <><th className="col-score">S</th><th className="col-score">O</th><th className="col-risk">Risk</th></>}
            {!hiddenColumns.has("status") && <th className="col-status">Review</th>}
          </tr>
        </thead>
        {groups.map((group) => (
          <tbody key={group.key} className={showCause ? "cause-group" : undefined}>
            {group.rows.map((row, rowInGroup) => {
              const displayIndex = ++counter;
              const isFirstInGroup = rowInGroup === 0;
              return (
                <tr
                  key={row.id}
                  className={row.id === selectedRow ? "is-selected" : ""}
                  onClick={() => onSelectRow(row.id)}
                >
                  <td className="row-index">
                    <button
                      className="row-selector"
                      aria-label={`${displayIndex}. select row`}
                      aria-pressed={row.id === selectedRow}
                    >
                      {displayIndex}
                    </button>
                  </td>
                  <td>
                    <select
                      aria-label={`${displayIndex}. row guideword`}
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
                      aria-label={`${displayIndex}. row deviation`}
                      value={row.deviation}
                      readOnly={readOnly}
                      onChange={(event) => onUpdateRow(row.id, "deviation", event.target.value)}
                    />
                  </td>
                  {/* Cause spans its consequence rows (item 7a): render once per group. */}
                  {showCause && isFirstInGroup && (
                    <td className="cause-cell" rowSpan={group.rows.length}>
                      <textarea
                        aria-label={`${displayIndex}. cause`}
                        value={row.cause}
                        readOnly={readOnly}
                        onChange={(event) =>
                          // Keep the group coherent: edit the cause on every
                          // consequence that shares it.
                          group.rows.forEach((r) => onUpdateRow(r.id, "cause", event.target.value))
                        }
                      />
                      {!readOnly && (
                        <button
                          type="button"
                          className="add-consequence"
                          onClick={(event) => {
                            event.stopPropagation();
                            onAddConsequence(row);
                          }}
                        >
                          ＋ consequence
                        </button>
                      )}
                    </td>
                  )}
                  <HazopConsequenceCells
                    row={row}
                    displayIndex={displayIndex}
                    readOnly={readOnly}
                    hiddenColumns={hiddenColumns}
                    onUpdateRow={onUpdateRow}
                  />
                </tr>
              );
            })}
          </tbody>
        ))}
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
  onOpenCitation,
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
  onOpenCitation: (citation: Suggestion["citations"][number]) => void;
}) {
  return (
    <aside className={`evidence-panel ${open ? "is-open" : ""}`} aria-label="Grounded suggestions">
      <div className="evidence-header">
        <div>
          <div className="panel-title">
            <Sparkles size={18} />
            <h2>Grounded suggestions</h2>
          </div>
          <p>
            {state === "ready" && suggestions.length > 0
              ? `${suggestions.length} cited passage${suggestions.length > 1 ? "s" : ""} · ${selectedRow?.deviation ?? ""}`
              : `Selected row: ${selectedRow?.deviation || "No deviation selected"}`}
          </p>
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
            <strong>Retrieve cited evidence for the selected deviation</strong>
            <p>Hybrid search over indexed standards and past studies — every passage is source-cited, nothing is generated.</p>
            <button
              className="primary-button"
              onClick={onRequest}
              disabled={!selectedRow || !canRequest}
            >
              Retrieve evidence
            </button>
          </div>
        )}
        {state === "loading" && (
          <div className="table-loading">Searching sources and validating citations...</div>
        )}
        {state === "error" && (
          <div className="functional-empty">
            <AlertTriangle size={26} />
            <strong>Grounded evidence could not be retrieved</strong>
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
        {suggestions.map((suggestion, index) => (
          <article className="suggestion-item" key={suggestion.id}>
            <div className="suggestion-meta">
              <span className="suggestion-kind kind-cause">Cited evidence · #{index + 1}</span>
              <span className="confidence">
                {{ Düşük: "Low", Orta: "Medium", Yüksek: "High" }[suggestion.confidence]} relevance
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
              <button
                className="text-button"
                onClick={() => suggestion.citations[0] && onOpenCitation(suggestion.citations[0])}
                disabled={suggestion.citations.length === 0}
              >
                Open source
              </button>
              <button
                className="apply-button"
                onClick={() => onApply(suggestion.id)}
                title="Append this passage to the Cause field with its source reference"
              >
                <Plus size={15} />
                Add as reference
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
function RiskMatrix({ studyId, canWrite, onError }: {
  studyId: string;
  canWrite: boolean;
  onError: (message: string) => void;
}) {
  const [settings, setSettings] = useState<RiskMatrixSettings | null>(null);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState({ low_max: 3, medium_max: 7, high_max: 11 });
  useEffect(() => {
    if (!studyId) return;
    fetchRiskMatrix(studyId).then((value) => {
      setSettings(value);
      setDraft(value);
    }).catch(() => onError("Risk matrix could not be loaded."));
  }, [studyId, onError]);
  const thresholds = settings ?? { low_max: 3, medium_max: 7, high_max: 11, revision: 1 };
  const riskZone = { low: "Low", medium: "Medium", high: "High", critical: "Critical" } as const;
  return (
    <section className="matrix-workspace">
      <div className="section-heading">
        <div>
          <h2>Client risk matrix</h2>
          <p>5 × 5 matrix · Revision {thresholds.revision} · controlled per study</p>
        </div>
        <button className="secondary-button" onClick={() => setEditing(true)} disabled={!canWrite}>Edit matrix</button>
      </div>
      <div className="matrix-layout">
        <div className="matrix-y-label">Likelihood</div>
        <div className="matrix-grid" role="grid" aria-label="5 by 5 risk matrix">
          {[5, 4, 3, 2, 1].map((likelihood) =>
            [1, 2, 3, 4, 5].map((severity) => {
              const score = likelihood * severity;
              const level = score > thresholds.high_max ? "critical" : score > thresholds.medium_max ? "high" : score > thresholds.low_max ? "medium" : "low";
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
      {editing && <div className="modal-backdrop" role="presentation">
        <form className="form-dialog" onSubmit={async (event) => {
          event.preventDefault();
          try {
            setSettings(await updateRiskMatrix(studyId, draft));
            setEditing(false);
          } catch (error) {
            onError(error instanceof Error ? error.message : "Risk matrix could not be updated.");
          }
        }}>
          <div className="dialog-heading">
            <div><h2>Edit risk thresholds</h2><p>Scores above each boundary move to the next risk band.</p></div>
            <button type="button" className="icon-button" onClick={() => setEditing(false)}><X size={18} /></button>
          </div>
          <label>Low maximum<input type="number" min="1" max="24" value={draft.low_max} onChange={(e) => setDraft({ ...draft, low_max: Number(e.target.value) })} /></label>
          <label>Medium maximum<input type="number" min="2" max="24" value={draft.medium_max} onChange={(e) => setDraft({ ...draft, medium_max: Number(e.target.value) })} /></label>
          <label>High maximum<input type="number" min="3" max="24" value={draft.high_max} onChange={(e) => setDraft({ ...draft, high_max: Number(e.target.value) })} /></label>
          <div className="dialog-actions">
            <button type="button" className="secondary-button" onClick={() => setEditing(false)}>Cancel</button>
            <button className="primary-button">Save revision</button>
          </div>
        </form>
      </div>}
    </section>
  );
}

function SourcesWorkspace({ studyId, canWrite, canDelete, onError }: {
  studyId: string;
  canWrite: boolean;
  canDelete: boolean;
  onError: (message: string) => void;
}) {
  const [sources, setSources] = useState<StudySource[]>([]);
  const [adding, setAdding] = useState(false);
  const [form, setForm] = useState({
    title: "",
    source_type: "Standard" as StudySource["source_type"],
    reference: "",
    section_count: 0,
  });
  useEffect(() => {
    if (studyId) {
      fetchSources(studyId).then(setSources).catch(() => onError("Study sources could not be loaded."));
    }
  }, [studyId, onError]);
  return (
    <section className="sources-workspace">
      <div className="section-heading">
        <div>
          <h2>Study sources</h2>
          <p>The controlled knowledge base available to the suggestion engine for this study.</p>
        </div>
        <button className="secondary-button" onClick={() => setAdding(true)} disabled={!canWrite}>
          <Plus size={16} />
          Add source
        </button>
      </div>
      <div className="source-list">
        {sources.map((source) => (
          <div className={`source-row ${source.is_active ? "" : "is-muted"}`} key={source.id}>
            <span className="source-icon">
              <BookOpen size={18} />
            </span>
            <div>
              <strong>{source.title}</strong>
              <span>{source.source_type}</span>
            </div>
            <span>{source.section_count} sections</span>
            <span>{source.is_active ? "Available to retrieval" : "Excluded from retrieval"}</span>
            <button className="text-button" disabled={!canWrite} onClick={async () => {
              try {
                const updated = await updateSource(source.id, { is_active: !source.is_active });
                setSources((items) => items.map((item) => item.id === source.id ? updated : item));
              } catch {
                onError("Source state could not be changed.");
              }
            }}>{source.is_active ? "Disable" : "Enable"}</button>
            {canDelete && <button className="icon-button" aria-label={`Delete ${source.title}`} onClick={async () => {
              if (!window.confirm(`Delete ${source.title}?`)) return;
              await deleteSource(source.id);
              setSources((items) => items.filter((item) => item.id !== source.id));
            }}><Trash2 size={16} /></button>}
          </div>
        ))}
      </div>
      {adding && <div className="modal-backdrop" role="presentation">
        <form className="form-dialog" onSubmit={async (event) => {
          event.preventDefault();
          try {
            const created = await createSource({ study_id: studyId, ...form });
            setSources((items) => [created, ...items]);
            setAdding(false);
            setForm({ title: "", source_type: "Standard", reference: "", section_count: 0 });
          } catch {
            onError("Source could not be added.");
          }
        }}>
          <div className="dialog-heading">
            <div><h2>Add controlled source</h2><p>Register the evidence available to this study.</p></div>
            <button type="button" className="icon-button" onClick={() => setAdding(false)}><X size={18} /></button>
          </div>
          <label>Title<input required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /></label>
          <label>Type<select value={form.source_type} onChange={(e) => setForm({ ...form, source_type: e.target.value as StudySource["source_type"] })}>{["Standard", "Historical study", "Procedure", "Drawing", "Other"].map((type) => <option key={type}>{type}</option>)}</select></label>
          <label>Reference<textarea value={form.reference} onChange={(e) => setForm({ ...form, reference: e.target.value })} /></label>
          <label>Indexed sections<input type="number" min="0" value={form.section_count} onChange={(e) => setForm({ ...form, section_count: Number(e.target.value) })} /></label>
          <div className="dialog-actions">
            <button type="button" className="secondary-button" onClick={() => setAdding(false)}>Cancel</button>
            <button className="primary-button">Add source</button>
          </div>
        </form>
      </div>}
    </section>
  );
}

function LibraryWorkspace({
  canWrite,
  canDelete,
  onApply,
  onError,
}: {
  canWrite: boolean;
  canDelete: boolean;
  onApply: (entry: LibraryEntry) => void;
  onError: (message: string) => void;
}) {
  const [entries, setEntries] = useState<LibraryEntry[]>([]);
  const [query, setQuery] = useState("");
  const [adding, setAdding] = useState(false);
  const [form, setForm] = useState({
    equipment_type: "", guideword: "Yok", deviation: "", cause: "", consequence: "",
    safeguard: "", severity: 3, likelihood: 2, source_ref: "",
  });
  const load = useCallback(
    () => fetchLibrary(query).then(setEntries).catch(() => onError("Scenario library could not be loaded.")),
    [query, onError],
  );
  useEffect(() => { void load(); }, [load]);
  return <section className="rail-section-page">
    <div className="section-heading">
      <div><h2>Scenario library</h2><p>Reusable, approved scenario patterns grouped by equipment type.</p></div>
      <button className="primary-button" onClick={() => setAdding(true)} disabled={!canWrite}><Plus size={16} />New library entry</button>
    </div>
    <label className="table-search library-search"><Search size={15} /><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search equipment, deviation or source" /></label>
    <div className="library-grid">
      {entries.map((entry) => <article className="library-card" key={entry.id}>
        <div className="library-card-head"><Badge variant="outline">{entry.equipment_type}</Badge><RiskBadge level={entry.risk} /></div>
        <h3>{entry.guideword} · {entry.deviation}</h3>
        <dl><div><dt>Cause</dt><dd>{entry.cause}</dd></div><div><dt>Consequence</dt><dd>{entry.consequence}</dd></div><div><dt>Safeguard</dt><dd>{entry.safeguard || "Not defined"}</dd></div></dl>
        <small>{entry.source_ref || "Internal approved pattern"}</small>
        <div className="library-actions">
          <button className="secondary-button compact" onClick={() => onApply(entry)} disabled={!canWrite}><Plus size={15} />Add to active node</button>
          {canDelete && <button className="icon-button" aria-label="Delete library entry" onClick={async () => {
            if (!window.confirm("Delete this library entry?")) return;
            await deleteLibraryEntry(entry.id);
            setEntries((items) => items.filter((item) => item.id !== entry.id));
          }}><Trash2 size={15} /></button>}
        </div>
      </article>)}
    </div>
    {adding && <div className="modal-backdrop" role="presentation"><form className="form-dialog wide-dialog" onSubmit={async (event) => {
      event.preventDefault();
      try {
        const created = await createLibraryEntry(form);
        setEntries((items) => [created, ...items]);
        setAdding(false);
      } catch { onError("Library entry could not be created."); }
    }}>
      <div className="dialog-heading"><div><h2>New scenario pattern</h2><p>Capture a reusable, reviewed scenario record.</p></div><button type="button" className="icon-button" onClick={() => setAdding(false)}><X size={18} /></button></div>
      <label>Equipment type<input required value={form.equipment_type} onChange={(e) => setForm({ ...form, equipment_type: e.target.value })} /></label>
      <label>Guideword<select value={form.guideword} onChange={(e) => setForm({ ...form, guideword: e.target.value })}>{["Yok", "Fazla", "Az", "Ters", "Başka"].map((word) => <option key={word}>{word}</option>)}</select></label>
      <label>Deviation<input required value={form.deviation} onChange={(e) => setForm({ ...form, deviation: e.target.value })} /></label>
      <label>Cause<textarea required value={form.cause} onChange={(e) => setForm({ ...form, cause: e.target.value })} /></label>
      <label>Consequence<textarea required value={form.consequence} onChange={(e) => setForm({ ...form, consequence: e.target.value })} /></label>
      <label>Safeguard<textarea value={form.safeguard} onChange={(e) => setForm({ ...form, safeguard: e.target.value })} /></label>
      <label>Source reference<input value={form.source_ref} onChange={(e) => setForm({ ...form, source_ref: e.target.value })} /></label>
      <div className="dialog-actions"><button type="button" className="secondary-button" onClick={() => setAdding(false)}>Cancel</button><button className="primary-button">Create entry</button></div>
    </form></div>}
  </section>;
}

function ReportsWorkspace({ studyId, nodeId, onError }: {
  studyId: string;
  nodeId: string;
  onError: (message: string) => void;
}) {
  const [reports, setReports] = useState<ReportEntry[]>([]);
  const load = useCallback(
    () => fetchReports().then(setReports).catch(() => onError("Report history could not be loaded.")),
    [onError],
  );
  useEffect(() => { void load(); }, [load]);
  return <section className="rail-section-page">
    <div className="section-heading">
      <div><h2>Reports</h2><p>Generated, editable HAZOP deliverables and their authorship trail.</p></div>
      <button className="primary-button" onClick={() => {
        window.location.href = reportUrl(studyId, nodeId);
        window.setTimeout(load, 1200);
      }} disabled={!studyId || !nodeId}><Download size={16} />Generate active node report</button>
    </div>
    <div className="history-table">
      <div className="history-head"><span>Report</span><span>Study / node</span><span>Created by</span><span>Date</span></div>
      {reports.map((report) => <div className="history-row" key={report.id}><strong>{report.filename}</strong><span>{report.study_title} · {report.node_name}</span><span>{report.created_by}</span><time>{new Date(report.created_at).toLocaleString()}</time></div>)}
      {reports.length === 0 && <div className="table-empty"><FileOutput size={28} /><strong>No reports generated yet</strong><p>Generate the active node report to create the first history record.</p></div>}
    </div>
  </section>;
}

function AuditWorkspace({ onError }: { onError: (message: string) => void }) {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [query, setQuery] = useState("");
  useEffect(() => { fetchAudit().then(setEntries).catch(() => onError("Audit history could not be loaded.")); }, [onError]);
  const filtered = entries.filter((entry) => `${entry.entity_type} ${entry.entity_id} ${entry.action}`.toLowerCase().includes(query.toLowerCase()));
  return <section className="rail-section-page">
    <div className="section-heading"><div><h2>Audit history</h2><p>Immutable create, update, delete and report events from the workspace backend.</p></div></div>
    <label className="table-search library-search"><Search size={15} /><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Filter history" /></label>
    <div className="history-table">
      <div className="history-head"><span>Entity</span><span>Action</span><span>Identifier</span><span>Date</span></div>
      {filtered.map((entry) => <div className="history-row" key={entry.id}><strong>{entry.entity_type.replace("_", " ")}</strong><Badge variant="outline">{entry.action}</Badge><span className="mono">{entry.entity_id}</span><time>{new Date(entry.created_at).toLocaleString()}</time></div>)}
    </div>
  </section>;
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
            The operational workspace is connected end to end. Managed PostgreSQL and
            the private AI corpus remain deployment-environment integrations.
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
            Supply managed PostgreSQL and private model credentials, then ingest the
            client-approved corpus for production-grounded assistance.
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
  onImported,
  onError,
}: {
  open: boolean;
  onClose: () => void;
  onCreated: (study: StudyListItem) => void;
  onImported: (result: OphaImportResult) => void;
  onError: (msg: string) => void;
}) {
  const [values, setValues] = useState({ title: "", client: "", facility: "" });
  const [saving, setSaving] = useState(false);
  const [importing, setImporting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  if (!open) return null;

  const handleImportFile = async (file: File) => {
    setImporting(true);
    try {
      const text = await file.text();
      const result = await importOphaStudy(text);
      onImported(result);
    } catch (error) {
      onError(
        error instanceof ApiError
          ? `The .opha file could not be imported: ${error.message}`
          : "The .opha file could not be imported. Check the file and API connection.",
      );
    } finally {
      setImporting(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

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
        <div className="import-opha-divider" role="separator">or import an existing study</div>
        <input
          ref={fileInputRef}
          type="file"
          accept=".opha,application/json"
          hidden
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void handleImportFile(file);
          }}
        />
        <button
          type="button"
          className="secondary-button import-opha-button"
          disabled={importing}
          onClick={() => fileInputRef.current?.click()}
        >
          <Upload size={16} /> {importing ? "Importing .opha..." : "Import OpenPHA (.opha) file"}
        </button>
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

function HelpDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  if (!open) return null;
  return <div className="modal-backdrop" role="presentation"><div className="form-dialog">
    <div className="dialog-heading"><div><h2>PreventA workspace guide</h2><p>Core controls for facilitated studies.</p></div><button className="icon-button" onClick={onClose}><X size={18} /></button></div>
    <div className="help-list">
      <div><kbd>Ctrl</kbd> + <kbd>Enter</kbd><span>Add a HAZOP row to the active node.</span></div>
      <div><BookOpen size={18} /><span>Use Scenario library to apply approved patterns as editable drafts.</span></div>
      <div><Sparkles size={18} /><span>Grounded suggestions require indexed corpus evidence and facilitator access.</span></div>
      <div><History size={18} /><span>Every material create, update, delete and report event appears in Audit history.</span></div>
    </div>
    <div className="dialog-actions"><button className="primary-button" onClick={onClose}>Close guide</button></div>
  </div></div>;
}

function SettingsDialog({ open, user, onClose, onError }: {
  open: boolean;
  user: AuthUser;
  onClose: () => void;
  onError: (message: string) => void;
}) {
  const [users, setUsers] = useState<AuthUser[]>([]);
  const [adding, setAdding] = useState(false);
  const [form, setForm] = useState({ email: "", full_name: "", password: "", role: "viewer" as AuthUser["role"] });
  useEffect(() => {
    if (open && user.role === "admin") fetchUsers().then(setUsers).catch(() => onError("Users could not be loaded."));
  }, [open, user.role, onError]);
  if (!open) return null;
  return <div className="modal-backdrop" role="presentation"><div className="form-dialog wide-dialog">
    <div className="dialog-heading"><div><h2>Workspace settings</h2><p>Account, access and local interface preferences.</p></div><button className="icon-button" onClick={onClose}><X size={18} /></button></div>
    <div className="account-summary"><Avatar><AvatarFallback>{user.full_name.slice(0, 2).toUpperCase()}</AvatarFallback></Avatar><div><strong>{user.full_name}</strong><span>{user.email} · {user.role}</span></div></div>
    <label className="setting-toggle"><input type="checkbox" defaultChecked onChange={(e) => localStorage.setItem("preventa-autosave", String(e.target.checked))} /><span><strong>Automatic draft saving</strong><small>Persist worksheet edits after a short debounce.</small></span></label>
    <label className="setting-toggle"><input type="checkbox" defaultChecked={localStorage.getItem("preventa-compact") === "true"} onChange={(e) => {
      localStorage.setItem("preventa-compact", String(e.target.checked));
      document.documentElement.classList.toggle("compact-workspace", e.target.checked);
    }} /><span><strong>Compact worksheet density</strong><small>Reduce row padding for facilitated sessions.</small></span></label>
    {user.role === "admin" && <div className="admin-users">
      <div className="section-heading"><div><h3>User access</h3><p>Administrators can provision role-controlled accounts.</p></div><button className="secondary-button compact" onClick={() => setAdding(true)}><Plus size={15} />Add user</button></div>
      {users.map((item) => <div className="user-access-row" key={item.id}><Avatar><AvatarFallback>{item.full_name.slice(0, 2).toUpperCase()}</AvatarFallback></Avatar><div><strong>{item.full_name}</strong><span>{item.email}</span></div><Badge variant="outline">{item.role}</Badge></div>)}
    </div>}
    <div className="dialog-actions"><button className="primary-button" onClick={onClose}>Done</button></div>
    {adding && <div className="nested-dialog"><form onSubmit={async (event) => {
      event.preventDefault();
      try {
        const created = await createUser(form);
        setUsers((items) => [...items, created]);
        setAdding(false);
        setForm({ email: "", full_name: "", password: "", role: "viewer" });
      } catch (error) { onError(error instanceof Error ? error.message : "User could not be created."); }
    }}>
      <div className="dialog-heading"><div><h3>Add user</h3><p>Password must contain at least 12 characters.</p></div><button type="button" className="icon-button" onClick={() => setAdding(false)}><X size={17} /></button></div>
      <label>Full name<input required value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} /></label>
      <label>Email<input type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></label>
      <label>Temporary password<input type="password" minLength={12} required value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} /></label>
      <label>Role<select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value as AuthUser["role"] })}><option value="viewer">Viewer</option><option value="facilitator">Facilitator</option><option value="admin">Administrator</option></select></label>
      <div className="dialog-actions"><button type="button" className="secondary-button" onClick={() => setAdding(false)}>Cancel</button><button className="primary-button">Create user</button></div>
    </form></div>}
  </div></div>;
}

function StudyInfoDialog({ open, study, canWrite, onClose, onSaved, onError }: {
  open: boolean;
  study: WorkspaceStudy;
  canWrite: boolean;
  onClose: () => void;
  onSaved: (study: StudyListItem) => void;
  onError: (message: string) => void;
}) {
  const [form, setForm] = useState({ title: study.title, client: study.client, facility: study.facility, status: "draft" });
  useEffect(() => setForm({ title: study.title, client: study.client, facility: study.facility, status: "draft" }), [study]);
  if (!open) return null;
  return <div className="modal-backdrop" role="presentation"><form className="form-dialog" onSubmit={async (event) => {
    event.preventDefault();
    try {
      onSaved(await updateStudy(study.id, form));
      onClose();
    } catch { onError("Study information could not be updated."); }
  }}>
    <div className="dialog-heading"><div><h2>Study information</h2><p>Controlled project context used across nodes and reports.</p></div><button type="button" className="icon-button" onClick={onClose}><X size={18} /></button></div>
    <label>Study name<input readOnly={!canWrite} value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /></label>
    <label>Client<input readOnly={!canWrite} value={form.client} onChange={(e) => setForm({ ...form, client: e.target.value })} /></label>
    <label>Facility<input readOnly={!canWrite} value={form.facility} onChange={(e) => setForm({ ...form, facility: e.target.value })} /></label>
    <label>Status<select disabled={!canWrite} value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}><option value="draft">Draft</option><option value="in_review">In review</option><option value="complete">Complete</option></select></label>
    <div className="dialog-actions"><button type="button" className="secondary-button" onClick={onClose}>Cancel</button>{canWrite && <button className="primary-button">Save changes</button>}</div>
  </form></div>;
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
  const [worksheetQuery, setWorksheetQuery] = useState("");
  const [hiddenColumns, setHiddenColumns] = useState<Set<string>>(new Set());
  const [studyInfoOpen, setStudyInfoOpen] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [openCitation, setOpenCitation] = useState<Suggestion["citations"][number] | null>(null);
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);
  const saveTimers = useRef<Record<string, number>>({});
  const canWrite = user.permissions.includes("workspace:write");
  const canDelete = user.permissions.includes("workspace:delete");
  const canUseRag = user.permissions.includes("rag:use");

  const selected = useMemo(
    () => rows.find((row) => row.id === selectedRow) ?? rows[0],
    [rows, selectedRow],
  );
  const visibleRows = useMemo(() => {
    const query = worksheetQuery.trim().toLowerCase();
    if (!query) return rows;
    return rows.filter((row) =>
      `${row.guideword} ${row.deviation} ${row.cause} ${row.consequence} ${row.safeguard} ${row.status}`
        .toLowerCase()
        .includes(query),
    );
  }, [rows, worksheetQuery]);

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

  const notify = useCallback((message: string, type: "success" | "error" = "success") => {
    setToast({ message, type });
    window.setTimeout(() => setToast(null), 2800);
  }, []);
  const notifyError = useCallback((message: string) => notify(message, "error"), [notify]);

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

  // Add another consequence beneath an existing cause (item 7a): the new row
  // inherits the cause's guideword/deviation/cause so it joins the same group.
  const addConsequence = async (fromRow: HazopRow) => {
    if (!activeNodeId) {
      notify("Create a node before adding a consequence.", "error");
      return;
    }
    try {
      const created = await createHazopRow(activeNodeId, {
        guideword: fromRow.guideword,
        deviation: fromRow.deviation,
        cause: fromRow.cause,
        consequence: "",
        safeguard: "",
        severity: 1,
        likelihood: 1,
        status: "Eksik",
      });
      setRows((current) => [...current, created]);
      setSelectedRow(created.id);
      notify("A consequence was added under the cause.");
    } catch {
      notify("The consequence could not be added. Check the API connection.", "error");
    }
  };

  const addFromLibrary = async (entry: LibraryEntry) => {
    if (!activeNodeId) {
      notify("Select a node before applying a library entry.", "error");
      return;
    }
    try {
      const created = await createHazopRow(activeNodeId, {
        guideword: entry.guideword,
        deviation: entry.deviation,
        cause: entry.cause,
        consequence: entry.consequence,
        safeguard: entry.safeguard,
        severity: entry.severity,
        likelihood: entry.likelihood,
        status: "Taslak",
      });
      setRows((current) => [...current, created]);
      setSelectedRow(created.id);
      setRailSection("studies");
      notify("Scenario pattern added to the active node as a draft.");
    } catch {
      notify("The scenario pattern could not be added.", "error");
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
    // Preserve traceability: every imported passage carries its source ref so
    // the worksheet entry stays auditable back to the standard/past study.
    const sourceRef = suggestion.citations[0]?.source_ref;
    const cited = sourceRef ? `${suggestion.text} [Kaynak: ${sourceRef}]` : suggestion.text;
    const existing = selected[suggestion.target];
    updateRow(
      selected.id,
      suggestion.target,
      existing ? `${existing}\n${cited}` : cited,
    );
    notify(
      sourceRef
        ? `Cited evidence added to row ${selected.id} (source: ${sourceRef}).`
        : `Cited evidence added to row ${selected.id}.`,
    );
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
      // Keyless retrieval-only path: hybrid dense+sparse search returns cited
      // source passages with no LLM generation, so it runs live on serverless.
      const chunks = await fetchDeviationEvidence({
        study_id: study.id,
        node_id: activeNode.id,
        equipment_type: activeNode.equipment_type,
        design_intent: activeNode.design_intent,
        parameter: selected.deviation.trim() || selected.guideword,
        guideword: selected.guideword,
        deviation: selected.deviation.trim() || `${selected.guideword} deviation`,
        existing_safeguards: selected.safeguard.trim() ? [selected.safeguard.trim()] : [],
      });
      // Rank order → relevance label (top hits = high-confidence grounding).
      const confidenceForRank = (index: number): Suggestion["confidence"] =>
        index < 2 ? "Yüksek" : index < 4 ? "Orta" : "Düşük";
      setWorkspaceSuggestions(
        chunks.map((chunk, index) => ({
          id: chunk.chunk_id,
          kind: "Neden",
          text: chunk.content,
          confidence: confidenceForRank(index),
          citations: [
            {
              chunk_id: chunk.chunk_id,
              source_ref: chunk.source_ref,
              section_ref: chunk.section_ref,
              excerpt: chunk.content.slice(0, 320),
            },
          ],
          target: "cause",
        })),
      );
      setEvidenceState("ready");
      setApiConnected(true);
    } catch (error) {
      setWorkspaceSuggestions([]);
      setEvidenceState("error");
      setEvidenceError(
        error instanceof ApiError && error.status === 401
          ? "Your session expired. Sign in again to retrieve grounded evidence."
          : "No grounded evidence is available yet. The safety corpus must be indexed for this deployment.",
      );
    }
  };

  return (
    <div className="app-shell">
      <AppRail
        active={railSection}
        onSelect={setRailSection}
        onHelp={() => setHelpOpen(true)}
        onSettings={() => setSettingsOpen(true)}
        user={user}
      />
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
        onOverview={() => {
          setRailSection("studies");
          setActiveTab("HAZOP");
          setNavOpen(false);
        }}
        onStudyInformation={() => {
          setStudyInfoOpen(true);
          setNavOpen(false);
        }}
        onRiskMatrix={() => {
          setRailSection("studies");
          setActiveTab("Risk matrix");
          setNavOpen(false);
        }}
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
          onHistory={() => setRailSection("history")}
        />

        <main id="main-content" className="main-workspace">
          {railSection === "library" ? (
            <LibraryWorkspace canWrite={canWrite} canDelete={canDelete} onApply={addFromLibrary} onError={notifyError} />
          ) : railSection === "reports" ? (
            <ReportsWorkspace studyId={study.id} nodeId={activeNode.id} onError={notifyError} />
          ) : railSection === "history" ? (
            <AuditWorkspace onError={notifyError} />
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
                query={worksheetQuery}
                onQueryChange={setWorksheetQuery}
                onOpenLibrary={() => setRailSection("library")}
                hiddenColumns={hiddenColumns}
                onToggleColumn={(column) => setHiddenColumns((current) => {
                  const next = new Set(current);
                  if (next.has(column)) next.delete(column); else next.add(column);
                  return next;
                })}
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
                  rows={visibleRows}
                  selectedRow={selectedRow}
                  onSelectRow={setSelectedRow}
                  onUpdateRow={updateRow}
                  onAddConsequence={addConsequence}
                  readOnly={!canWrite}
                  hiddenColumns={hiddenColumns}
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
                  onOpenCitation={setOpenCitation}
                />
              </div>
            </>
          )}
          {activeTab === "LOPA" && (
            <LopaWorkspace selectedRow={selected} readOnly={!canWrite} />
          )}
          {activeTab === "Risk matrix" && <RiskMatrix studyId={study.id} canWrite={canWrite} onError={notifyError} />}
          {activeTab === "Sources" && <SourcesWorkspace studyId={study.id} canWrite={canWrite} canDelete={canDelete} onError={notifyError} />}
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
              Connected workspace data
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
        onImported={async (result) => {
          setStudyDialogOpen(false);
          try {
            const studies = await fetchStudies();
            setStudyOptions(studies);
            const imported = studies.find((item) => item.id === result.study_id);
            if (imported) {
              setStudy({
                ...imported,
                progress: 0,
                reviewed_scenarios: 0,
                total_scenarios: 0,
              });
              const studyNodes = await fetchNodes(result.study_id);
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
            }
            setApiConnected(true);
          } catch {
            notify("Study imported, but the workspace could not be refreshed.", "error");
            return;
          }
          const droppedTotal = Object.values(result.dropped).reduce((sum, n) => sum + n, 0);
          notify(
            `Imported "${result.study_title}": ${result.nodes} nodes, ${result.rows} scenarios, ` +
              `${result.lopa_layers} LOPA layers. ${droppedTotal} data points from the OpenPHA ` +
              `model could not be mapped to the flat worksheet.`,
          );
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
      <HelpDialog open={helpOpen} onClose={() => setHelpOpen(false)} />
      <SettingsDialog
        open={settingsOpen}
        user={user}
        onClose={() => setSettingsOpen(false)}
        onError={notifyError}
      />
      <StudyInfoDialog
        open={studyInfoOpen}
        study={study}
        canWrite={canWrite}
        onClose={() => setStudyInfoOpen(false)}
        onError={notifyError}
        onSaved={(updated) => {
          setStudy((current) => ({ ...current, ...updated }));
          setStudyOptions((items) => items.map((item) => item.id === updated.id ? updated : item));
          notify("Study information updated.");
        }}
      />
      {openCitation && <div className="modal-backdrop" role="presentation"><div className="form-dialog">
        <div className="dialog-heading"><div><h2>{openCitation.source_ref}</h2><p>{openCitation.section_ref ?? "Section not specified"}</p></div><button className="icon-button" onClick={() => setOpenCitation(null)}><X size={18} /></button></div>
        <div className="grounding-note"><FileClock size={17} /><span>Retrieved evidence excerpt</span></div>
        <p className="citation-excerpt">{openCitation.excerpt}</p>
        <div className="dialog-actions"><button className="primary-button" onClick={() => setOpenCitation(null)}>Close source</button></div>
      </div></div>}
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
