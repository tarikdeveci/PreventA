import type {
  HazopRow,
  ProductStatus,
  StudyListItem,
  WorkspaceNode,
  WorkspaceResponse,
} from "./data";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    throw new Error(`API request failed with ${response.status}`);
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
    headers: payload
      ? { Accept: "application/json", "Content-Type": "application/json" }
      : { Accept: "application/json" },
    body: payload ? JSON.stringify(payload) : undefined,
  });
  if (!response.ok) {
    throw new Error(`API request failed with ${response.status}`);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export function fetchWorkspace(): Promise<WorkspaceResponse> {
  return getJson<WorkspaceResponse>("/api/v1/workspace");
}

export function fetchProductStatus(): Promise<ProductStatus> {
  return getJson<ProductStatus>("/api/v1/status");
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

export function reportUrl(studyId: string, nodeId: string): string {
  return `${API_BASE}/api/v1/studies/${studyId}/nodes/${nodeId}/report.docx`;
}
