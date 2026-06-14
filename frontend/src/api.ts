import type {
  AuthUser,
  DeviationAssistRequest,
  DeviationAssistResponse,
  HazopRow,
  LopaLayer,
  ProductStatus,
  StudyListItem,
  WorkspaceNode,
  WorkspaceResponse,
  SessionResponse,
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
  method: "POST" | "PATCH" | "DELETE",
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

export function createHazopRow(nodeId: string): Promise<HazopRow> {
  return sendJson(`/api/v1/nodes/${nodeId}/rows`, "POST", {});
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

export function deleteNode(nodeId: string): Promise<void> {
  return sendJson(`/api/v1/nodes/${nodeId}`, "DELETE");
}

export function reportUrl(studyId: string, nodeId: string): string {
  return `${API_BASE}/api/v1/studies/${studyId}/nodes/${nodeId}/report.docx`;
}
