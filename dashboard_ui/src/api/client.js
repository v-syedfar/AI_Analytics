/**
 * API client for Planning Intelligence Azure Function backend.
 * Set REACT_APP_API_URL and REACT_APP_API_KEY in .env
 */

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:7071/api";
const API_KEY = process.env.REACT_APP_API_KEY || "";

export async function fetchDashboard(payload) {
  const res = await fetch(`${API_URL}/planning-dashboard-v2${API_KEY ? `?code=${API_KEY}` : ""}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
