import { components } from "./api-types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_BASE ||
  "http://127.0.0.1:8001";

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers = new Headers(init.headers || {});
  if (!headers.has("Content-Type") && init.body)
    headers.set("Content-Type", "application/json");
  if (token && !headers.has("Authorization"))
    headers.set("Authorization", `Bearer ${token}`);
  const apiKey = process.env.NEXT_PUBLIC_INTERNAL_API_KEY;
  if (apiKey && !headers.has("X-API-Key")) headers.set("X-API-Key", apiKey);
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Request failed: ${res.status}`);
  }
  const ct = res.headers.get("content-type") || "";
  return (
    ct.includes("application/json") ? res.json() : (undefined as unknown)
  ) as T;
}

export type LeadOut = components["schemas"]["LeadOut"];
export type TaskOut = components["schemas"]["TaskOut"];
export type LeadUpdate = components["schemas"]["LeadUpdate"];
export type TaskUpdate = components["schemas"]["TaskUpdate"];
export type AgentRunRequest = components["schemas"]["AgentRunRequest"];
export type ArtifactOut = components["schemas"]["ArtifactOut"];
