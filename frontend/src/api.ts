import type {
  AuthUser,
  DeviationAssistRequest,
  DeviationAssistResponse,
  RetrievedChunk,
  HazopRow,
  LopaLayer,
  ProductStatus,
  StudyListItem,
  WorkspaceNode,
  WorkspaceResponse,
  SessionResponse,
  LibraryEntry,
  StudySource,
  RiskMatrixSettings,
  AuditEntry,
  ReportEntry,
} from "./data";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string | undefined,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function apiError(response: Response): Promise<ApiError> {
  const payload = await response.json().catch(() => null) as {
    detail?: string | { code?: string; message?: string };
  } | null;
  const detail = payload?.detail;
  if (typeof detail === "object" && detail !== null) {
    return new ApiError(
      response.status,
      detail.code,
      detail.message ?? `API request failed with ${response.status}`,
    );
  }
  return new ApiError(
    response.status,
    undefined,
    typeof detail === "string" ? detail : `API request failed with ${response.status}`,
  );
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    throw await apiError(response);
  }
  return response.json() as Promise<T>;
}

async function sendJson<T>(
  path: string,
  method: "POST" | "PATCH" | "PUT" | "DELETE",
  payload?: unknown,
): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    credentials: "include",
    headers: payload
      ? { Accept: "application/json", "Content-Type": "application/json" }
      : { Accept: "application/json" },
    body: payload ? JSON.stringify(payload) : undefined,
  });
  if (!response.ok) {
    throw await apiError(response);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export function fetchSession(): Promise<SessionResponse> {
  return getJson("/api/v1/auth/me");
}

export function login(
  email: string,
  password: string,
): Promise<SessionResponse> {
  return sendJson("/api/v1/auth/login", "POST", { email, password });
}

export function logout(): Promise<void> {
  return sendJson("/api/v1/auth/logout", "POST");
}

export function fetchUsers(): Promise<AuthUser[]> {
  return getJson("/api/v1/auth/users");
}

export function fetchWorkspace(): Promise<WorkspaceResponse> {
  return getJson<WorkspaceResponse>("/api/v1/workspace");
}

export function fetchProductStatus(): Promise<ProductStatus> {
  return getJson<ProductStatus>("/api/v1/status");
}

export function fetchDeviationAssist(
  payload: DeviationAssistRequest,
): Promise<DeviationAssistResponse> {
  return sendJson("/api/v1/rag/deviation-assist", "POST", payload);
}

// Keyless retrieval: cited evidence for a deviation, no generation model needed.
export function fetchDeviationEvidence(
  payload: DeviationAssistRequest,
): Promise<RetrievedChunk[]> {
  return sendJson("/api/v1/rag/deviation-evidence", "POST", payload);
}

export function fetchStudies(): Promise<StudyListItem[]> {
  return getJson("/api/v1/studies");
}

export function createStudy(payload: {
  title: string;
  client: string;
  facility: string;
}): Promise<StudyListItem> {
  return sendJson("/api/v1/studies", "POST", payload);
}

export function updateStudy(
  studyId: string,
  payload: Partial<Pick<StudyListItem, "title" | "client" | "facility" | "status">>,
): Promise<StudyListItem> {
  return sendJson(`/api/v1/studies/${studyId}`, "PATCH", payload);
}

export function fetchNodes(studyId: string): Promise<WorkspaceNode[]> {
  return getJson(`/api/v1/studies/${studyId}/nodes`);
}

export function createNode(
  studyId: string,
  payload: {
    code: string;
    name: string;
    equipment_type: string;
    design_intent: string;
  },
): Promise<WorkspaceNode> {
  return sendJson(`/api/v1/studies/${studyId}/nodes`, "POST", payload);
}

export function fetchRows(nodeId: string): Promise<HazopRow[]> {
  return getJson(`/api/v1/nodes/${nodeId}/rows`);
}

export function createHazopRow(
  nodeId: string,
  payload: Partial<Omit<HazopRow, "id" | "risk">> = {},
): Promise<HazopRow> {
  return sendJson(`/api/v1/nodes/${nodeId}/rows`, "POST", payload);
}

export function updateHazopRow(
  rowId: number,
  payload: Partial<HazopRow>,
): Promise<HazopRow> {
  return sendJson(`/api/v1/rows/${rowId}`, "PATCH", payload);
}

export function deleteHazopRow(rowId: number): Promise<void> {
  return sendJson(`/api/v1/rows/${rowId}`, "DELETE");
}

export function fetchLopaLayers(rowId: number): Promise<LopaLayer[]> {
  return getJson(`/api/v1/rows/${rowId}/lopa`);
}

export function addLopaLayer(
  rowId: number,
  payload: { description: string; pfd: number; is_valid: boolean; note: string },
): Promise<LopaLayer> {
  return sendJson(`/api/v1/rows/${rowId}/lopa`, "POST", payload);
}

export function deleteLopaLayer(layerId: string): Promise<void> {
  return sendJson(`/api/v1/lopa/${layerId}`, "DELETE");
}

export function deleteStudy(studyId: string): Promise<void> {
  return sendJson(`/api/v1/studies/${studyId}`, "DELETE");
}

export interface OphaImportResult {
  study_id: string;
  study_title: string;
  nodes: number;
  rows: number;
  lopa_layers: number;
  dropped: Record<string, number>;
}

export async function importOphaStudy(fileText: string): Promise<OphaImportResult> {
  const response = await fetch(`${API_BASE}/api/v1/studies/import`, {
    method: "POST",
    credentials: "include",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: fileText,
  });
  if (!response.ok) {
    throw await apiError(response);
  }
  return response.json() as Promise<OphaImportResult>;
}

export function deleteNode(nodeId: string): Promise<void> {
  return sendJson(`/api/v1/nodes/${nodeId}`, "DELETE");
}

export function reportUrl(studyId: string, nodeId: string): string {
  return `${API_BASE}/api/v1/studies/${studyId}/nodes/${nodeId}/report.docx`;
}

export function fetchLibrary(query = ""): Promise<LibraryEntry[]> {
  return getJson(`/api/v1/library${query ? `?q=${encodeURIComponent(query)}` : ""}`);
}

export function createLibraryEntry(
  payload: Omit<LibraryEntry, "id" | "risk">,
): Promise<LibraryEntry> {
  return sendJson("/api/v1/library", "POST", payload);
}

export function deleteLibraryEntry(entryId: string): Promise<void> {
  return sendJson(`/api/v1/library/${entryId}`, "DELETE");
}

export function fetchSources(studyId: string): Promise<StudySource[]> {
  return getJson(`/api/v1/studies/${studyId}/sources`);
}

export function createSource(
  payload: Omit<StudySource, "id" | "is_active" | "indexed_at">,
): Promise<StudySource> {
  return sendJson("/api/v1/sources", "POST", payload);
}

export function updateSource(
  sourceId: string,
  payload: Partial<StudySource>,
): Promise<StudySource> {
  return sendJson(`/api/v1/sources/${sourceId}`, "PATCH", payload);
}

export function deleteSource(sourceId: string): Promise<void> {
  return sendJson(`/api/v1/sources/${sourceId}`, "DELETE");
}

export function fetchRiskMatrix(studyId: string): Promise<RiskMatrixSettings> {
  return getJson(`/api/v1/studies/${studyId}/risk-matrix`);
}

export function updateRiskMatrix(
  studyId: string,
  payload: Pick<RiskMatrixSettings, "low_max" | "medium_max" | "high_max">,
): Promise<RiskMatrixSettings> {
  return sendJson(`/api/v1/studies/${studyId}/risk-matrix`, "PUT", payload);
}

export function fetchAudit(): Promise<AuditEntry[]> {
  return getJson("/api/v1/audit");
}

export function fetchReports(): Promise<ReportEntry[]> {
  return getJson("/api/v1/reports");
}

export function createUser(payload: {
  email: string;
  full_name: string;
  password: string;
  role: AuthUser["role"];
}): Promise<AuthUser> {
  return sendJson("/api/v1/auth/users", "POST", payload);
}
