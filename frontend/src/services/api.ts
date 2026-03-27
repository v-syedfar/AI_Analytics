import { DashboardResponse } from "../types/dashboard";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:7071/api";
const API_KEY = process.env.REACT_APP_API_KEY || "";

const headers = {
  "Content-Type": "application/json",
  ...(API_KEY ? { "x-functions-key": API_KEY } : {}),
};

function endpoint(path: string): string {
  return `${API_URL}/${path}${API_KEY ? `?code=${API_KEY}` : ""}`;
}

export async function fetchDashboard(payload: {
  mode?: "live" | "cached" | "sharepoint";
  location_id?: string;
  material_group?: string;
  current_rows?: object[];
  previous_rows?: object[];
}): Promise<DashboardResponse> {
  const res = await fetch(endpoint("planning-dashboard-v2"), {
    method: "POST",
    headers,
    body: JSON.stringify({ mode: "cached", ...payload }),
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
  return res.json();
}

export async function fetchExplain(payload: {
  question: string;
  mode?: "live" | "cached";
  location_id?: string;
  material_group?: string;
}): Promise<{
  question: string;
  aiInsight: string;
  rootCause: string;
  recommendedActions: string[];
  alerts: object;
  drivers: object;
  planningHealth: number;
}> {
  const res = await fetch(endpoint("explain"), {
    method: "POST",
    headers,
    body: JSON.stringify({ mode: "cached", ...payload }),
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

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
    body: JSON.stringify({}),
  });
  if (!res.ok) throw new Error(`Refresh failed: ${res.status}`);
  return res.json();
}
