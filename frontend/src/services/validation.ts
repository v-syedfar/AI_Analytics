import { DashboardResponse } from "../types/dashboard";

const REQUIRED_FIELDS: Array<{ key: keyof DashboardResponse; type: string }> = [
  { key: "dataMode", type: "string" },
  { key: "planningHealth", type: "number" },
  { key: "status", type: "string" },
  { key: "forecastNew", type: "number" },
  { key: "forecastOld", type: "number" },
  { key: "trendDirection", type: "string" },
  { key: "trendDelta", type: "number" },
  { key: "totalRecords", type: "number" },
  { key: "changedRecordCount", type: "number" },
  { key: "riskSummary", type: "object" },
  { key: "aiInsight", type: "string" },
  { key: "rootCause", type: "string" },
  { key: "recommendedActions", type: "array" },
  { key: "drivers", type: "object" },
  { key: "alerts", type: "object" },
  { key: "filters", type: "object" },
];

/**
 * Pure validation function — never throws, never mutates.
 * Logs console.warn for each missing or type-mismatched field.
 * Returns true if all required fields are present with correct types.
 */
export function validateDashboardResponse(data: unknown): data is DashboardResponse {
  if (data === null || data === undefined || typeof data !== "object") {
    console.warn("[validateDashboardResponse] Response is null, undefined, or not an object");
    return false;
  }

  const obj = data as Record<string, unknown>;
  let valid = true;

  for (const { key, type } of REQUIRED_FIELDS) {
    const value = obj[key];
    if (value === undefined || value === null) {
      console.warn(`[validateDashboardResponse] Missing required field: ${key}`);
      valid = false;
    } else if (type === "array") {
      if (!Array.isArray(value)) {
        console.warn(`[validateDashboardResponse] Field "${key}" expected array, got "${typeof value}"`);
        valid = false;
      }
    } else if (typeof value !== type) {
      console.warn(
        `[validateDashboardResponse] Field "${key}" expected type "${type}", got "${typeof value}"`
      );
      valid = false;
    }
  }

  return valid;
}
