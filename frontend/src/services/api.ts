import { DashboardResponse, DashboardContext, ExplainResponse, DebugSnapshotResponse } from "../types/dashboard";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:7071/api";
const API_KEY = process.env.REACT_APP_API_KEY || "";

function endpoint(path: string): string {
  return `${API_URL}/${path}${API_KEY ? `?code=${API_KEY}` : ""}`;
}

const headers = { "Content-Type": "application/json" };

/**
 * Fetches dashboard data from blob-backed backend.
 * Uses cached snapshot by default; falls back to blob reload if no snapshot.
 */
export async function fetchDashboard(payload?: {
  location_id?: string;
  material_group?: string;
}): Promise<DashboardResponse> {
  const res = await fetch(endpoint("planning-dashboard-v2"), {
    method: "POST",
    headers,
    body: JSON.stringify({ mode: "blob", ...payload }),
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
  return res.json();
}

/**
 * Sends a question to the explain endpoint with current dashboard context.
 * All answers are grounded in blob-derived analysis data.
 */
export async function fetchExplain(payload: {
  question: string;
  location_id?: string;
  material_group?: string;
  context?: Partial<DashboardContext>;
}): Promise<ExplainResponse> {
  const res = await fetch(endpoint("explain"), {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

/**
 * Fetches debug snapshot with intermediate pipeline values.
 */
export async function fetchDebugSnapshot(params?: {
  location_id?: string;
  material_group?: string;
}): Promise<DebugSnapshotResponse> {
  const res = await fetch(endpoint("debug-snapshot"), {
    method: "POST",
    headers,
    body: JSON.stringify({ mode: "blob", ...params }),
  });
  if (!res.ok) throw new Error(`Debug snapshot error ${res.status}: ${await res.text()}`);
  return res.json();
}

/**
 * Triggers daily refresh from Blob Storage.
 */
export async function triggerDailyRefresh(): Promise<{
  status: string;
  lastRefreshedAt: string;
  totalRecords: number;
  changedRecordCount: number;
  planningHealth: number;
}> {
  const res = await fetch(endpoint("daily-refresh"), {
    method: "POST",
    headers,
    body: JSON.stringify({ source: "blob" }),
  });
  if (!res.ok) throw new Error(`Refresh failed: ${res.status}`);
  return res.json();
}
