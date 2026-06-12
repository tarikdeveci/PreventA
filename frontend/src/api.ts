import type { ProductStatus, WorkspaceResponse } from "./data";

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

export function fetchWorkspace(): Promise<WorkspaceResponse> {
  return getJson<WorkspaceResponse>("/api/v1/workspace");
}

export function fetchProductStatus(): Promise<ProductStatus> {
  return getJson<ProductStatus>("/api/v1/status");
}

