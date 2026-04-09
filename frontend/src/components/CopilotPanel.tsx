import React, { useState, useRef, useEffect, useCallback } from "react";
import { DashboardContext, DashboardResponse } from "../types/dashboard";
import { fetchExplain } from "../services/api";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: number;
  followUps?: string[];
}

interface CopilotPanelProps {
  isOpen: boolean;
  onClose: () => void;
  context: DashboardContext;
  selectedEntity?: { type: string; item: string } | null;
  fullData?: DashboardResponse | null;
}

// ---------------------------------------------------------------------------
// Context label for header
// ---------------------------------------------------------------------------
function contextLabel(entity?: { type: string; item: string } | null): string {
  if (!entity) return "Global Analysis";
  const labels: Record<string, string> = { location: "Location", material: "Material Group", supplier: "Supplier", risk: "Risk" };
  return `${labels[entity.type] ?? entity.type}: ${entity.item}`;
}

// ---------------------------------------------------------------------------
// Dynamic smart prompts — business-oriented, data-aware
// ---------------------------------------------------------------------------

interface PromptCandidate {
  text: string;
  relevance: number; // 0-100, higher = more relevant
  category: string;
}

function buildSmartPrompts(ctx: DashboardContext, entity?: { type: string; item: string } | null): string[] {
  const candidates: PromptCandidate[] = [];

  if (entity) {
    return buildEntityPrompts(ctx, entity);
  }

  // --- Health & Summary ---
  if (ctx.planningHealth < 40) {
    candidates.push({ text: `Why is planning health critical at ${ctx.planningHealth}/100?`, relevance: 95, category: "health" });
  } else if (ctx.planningHealth < 60) {
    candidates.push({ text: `Why is planning health at risk (${ctx.planningHealth}/100)?`, relevance: 85, category: "health" });
  } else {
    candidates.push({ text: "What is the current planning health?", relevance: 50, category: "health" });
  }

  // --- Trend / Forecast ---
  if (ctx.trendDelta > 0) {
    candidates.push({ text: `Why did forecast increase by +${ctx.trendDelta?.toLocaleString()} units?`, relevance: 80, category: "forecast" });
  } else if (ctx.trendDelta < 0) {
    candidates.push({ text: `Why did forecast decrease by ${ctx.trendDelta?.toLocaleString()} units?`, relevance: 80, category: "forecast" });
  }
  candidates.push({ text: "Where are we seeing new demand surges?", relevance: (ctx as any).kpis?.newDemandRatio > 5 ? 75 : 30, category: "forecast" });

  // --- Supplier ---
  if ((ctx.riskSummary?.supplierChangedCount ?? 0) > 0) {
    candidates.push({ text: "Which suppliers are appearing in changed records?", relevance: 80, category: "supplier" });
    candidates.push({ text: "Which supplier has the most frequent design changes?", relevance: 70, category: "supplier" });
    if (ctx.drivers?.supplier) {
      candidates.push({ text: `Why is supplier ${ctx.drivers.supplier} risky?`, relevance: 85, category: "supplier" });
    }
  }
  candidates.push({ text: "Where is forecast increase not matched by supplier readiness?", relevance: ctx.supplierSummary?.changed > 0 ? 65 : 20, category: "supplier" });

  // --- Design Changes ---
  if ((ctx.riskSummary?.designChangedCount ?? 0) > 0) {
    candidates.push({ text: "Which materials have BOD or Form Factor changes?", relevance: 85, category: "design" });
    candidates.push({ text: "Which supplier has the most design changes?", relevance: 70, category: "design" });
  }

  // --- ROJ / Schedule ---
  if ((ctx.riskSummary?.rojChangedCount ?? 0) > 0) {
    candidates.push({ text: "Which locations have ROJ delays?", relevance: 80, category: "schedule" });
    candidates.push({ text: "Which supplier is failing to meet ROJ need-by dates?", relevance: 75, category: "schedule" });
  }

  // --- Location ---
  const topLoc = (ctx.datacenterSummary ?? []).sort((a, b) => b.changed - a.changed)[0];
  if (topLoc && topLoc.changed > 0) {
    candidates.push({ text: `Why is ${topLoc.locationId} changing the most?`, relevance: 85, category: "location" });
  }
  candidates.push({ text: "Which locations need immediate planner attention?", relevance: 70, category: "location" });

  // --- Material Group ---
  const topMg = (ctx.materialGroupSummary ?? []).sort((a, b) => b.changed - a.changed)[0];
  if (topMg && topMg.changed > 0) {
    candidates.push({ text: `Why is ${topMg.materialGroup} the most impacted group?`, relevance: 75, category: "material" });
  }

  // --- Risk / Action ---
  if ((ctx.highRiskRecordCount ?? 0) > 0) {
    candidates.push({ text: "Which records are highest risk right now?", relevance: 90, category: "risk" });
  }
  candidates.push({ text: "What are the top planner actions for this cycle?", relevance: 75, category: "action" });
  candidates.push({ text: "Which issues are likely to escalate?", relevance: 60, category: "action" });

  // --- Provenance ---
  candidates.push({ text: "What data source is being used?", relevance: 20, category: "provenance" });

  // --- Comparison ---
  const topLocs2 = (ctx.datacenterSummary ?? []).sort((a, b) => b.changed - a.changed);
  if (topLocs2.length >= 2) {
    candidates.push({ text: `Compare ${topLocs2[0].locationId} vs ${topLocs2[1].locationId}`, relevance: 70, category: "comparison" });
  }

  // --- Traceability ---
  candidates.push({ text: "Show top contributing records", relevance: 55, category: "traceability" });

  // Sort by relevance, pick top 6, ensure category diversity
  return selectDiversePrompts(candidates, 6);
}

function buildEntityPrompts(ctx: DashboardContext, entity: { type: string; item: string }): string[] {
  const { type, item } = entity;
  const candidates: PromptCandidate[] = [];

  // Universal entity prompts
  candidates.push({ text: `Why is ${item} showing changes?`, relevance: 90, category: "summary" });
  candidates.push({ text: `What is the risk level for ${item}?`, relevance: 85, category: "risk" });
  candidates.push({ text: `What actions should be taken for ${item}?`, relevance: 80, category: "action" });

  if (type === "location") {
    candidates.push({ text: `Which material groups changed at ${item}?`, relevance: 85, category: "material" });
    candidates.push({ text: `Which suppliers are impacted at ${item}?`, relevance: 75, category: "supplier" });
    if ((ctx.riskSummary?.rojChangedCount ?? 0) > 0) {
      candidates.push({ text: `Are there ROJ delays at ${item}?`, relevance: 80, category: "schedule" });
    }
    if ((ctx.riskSummary?.designChangedCount ?? 0) > 0) {
      candidates.push({ text: `Any design changes at ${item}?`, relevance: 75, category: "design" });
    }
    candidates.push({ text: `Is ${item} a change hotspot?`, relevance: 65, category: "summary" });
  }

  if (type === "material") {
    candidates.push({ text: `Which locations are affected by ${item}?`, relevance: 85, category: "location" });
    candidates.push({ text: `Is ${item} demand-driven or design-driven?`, relevance: 80, category: "forecast" });
    if ((ctx.riskSummary?.designChangedCount ?? 0) > 0) {
      candidates.push({ text: `Any BOD or Form Factor changes in ${item}?`, relevance: 80, category: "design" });
    }
    candidates.push({ text: `Is ${item} demand-driven or design-driven?`, relevance: 65, category: "summary" });
  }

  if (type === "supplier") {
    candidates.push({ text: `Is ${item} reliable?`, relevance: 85, category: "supplier" });
    candidates.push({ text: `What materials does ${item} impact?`, relevance: 80, category: "material" });
    candidates.push({ text: `Is ${item} meeting ROJ need-by dates?`, relevance: 75, category: "schedule" });
    candidates.push({ text: `Does ${item} have design change issues?`, relevance: 70, category: "design" });
    candidates.push({ text: `Which locations depend on ${item}?`, relevance: 70, category: "location" });
  }

  if (type === "risk") {
    candidates.push({ text: `Which locations have ${item}?`, relevance: 85, category: "location" });
    candidates.push({ text: `Which suppliers contribute to ${item}?`, relevance: 80, category: "supplier" });
    candidates.push({ text: `How many records are classified as ${item}?`, relevance: 75, category: "summary" });
    candidates.push({ text: `Show top records with ${item}`, relevance: 65, category: "traceability" });
  }

  return selectDiversePrompts(candidates, 6);
}

function selectDiversePrompts(candidates: PromptCandidate[], maxCount: number): string[] {
  // Sort by relevance descending
  const sorted = [...candidates].sort((a, b) => b.relevance - a.relevance);
  const selected: PromptCandidate[] = [];
  const usedCategories = new Set<string>();

  // First pass: pick highest relevance per category
  for (const c of sorted) {
    if (selected.length >= maxCount) break;
    if (!usedCategories.has(c.category)) {
      selected.push(c);
      usedCategories.add(c.category);
    }
  }

  // Second pass: fill remaining slots with highest relevance regardless of category
  for (const c of sorted) {
    if (selected.length >= maxCount) break;
    if (!selected.includes(c)) {
      selected.push(c);
    }
  }

  return selected.map(c => c.text);
}

// ---------------------------------------------------------------------------
// Follow-up suggestions
// ---------------------------------------------------------------------------
function buildFollowUps(question: string, ctx: DashboardContext, entity?: { type: string; item: string } | null): string[] {
  const q = question.toLowerCase();
  const suggestions: string[] = [];
  if (q.includes("health") || q.includes("critical")) {
    suggestions.push("What is driving the risk?", "Which locations are most impacted?", "What actions should be taken?");
  } else if (q.includes("change") || q.includes("driver")) {
    suggestions.push("Is this demand-driven or design-driven?", "Show top risk areas", "What should the planner do?");
  } else if (q.includes("supplier")) {
    suggestions.push("Which materials are affected?", "Is there a schedule delay?", "What is the supplier reliability?");
  } else if (q.includes("location") || q.includes("datacenter")) {
    suggestions.push("Which material groups changed here?", "What is the forecast delta?", "Any design changes?");
  } else if (q.includes("forecast") || q.includes("demand")) {
    suggestions.push("Is this a spike or a trend?", "Which locations drive the increase?", "What actions are recommended?");
  } else if (q.includes("design") || q.includes("bod")) {
    suggestions.push("Which materials have design changes?", "Is this BOD or Form Factor?", "What is the procurement impact?");
  } else {
    suggestions.push("What changed most?", "Show KPI summary", "What should the planner do next?");
  }
  return suggestions.slice(0, 3);
}

// ---------------------------------------------------------------------------
// Greeting
// ---------------------------------------------------------------------------
function buildGreeting(ctx: DashboardContext, entity?: { type: string; item: string } | null): string {
  const mockNote = ctx.dataMode === "mock" ? "\n⚠️ Running in test mode using mock data.\n" : "";
  if (entity) {
    return (
      `🔍 Focused on ${contextLabel(entity)}\n${mockNote}\n` +
      `📊 Health: ${ctx.planningHealth}/100 (${ctx.status})\n` +
      `📦 Changed: ${ctx.changedRecordCount} of ${ctx.totalRecords}\n` +
      `⚠️ Risk: ${ctx.riskSummary?.level ?? "N/A"}\n\n` +
      `Ask me about this ${entity.type} — why it changed, risk level, or recommended actions.`
    );
  }
  const insight = ctx.aiInsight ? ctx.aiInsight.slice(0, 150) + (ctx.aiInsight.length > 150 ? "…" : "") : "N/A";
  return (
    `📊 Planning Copilot — ${ctx.dataMode === "mock" ? "Mock Mode" : "Blob-backed Analysis"}\n${mockNote}\n` +
    `Health: ${ctx.planningHealth}/100 (${ctx.status})\n` +
    `Changed: ${ctx.changedRecordCount} of ${ctx.totalRecords} records\n` +
    `Risk: ${ctx.riskSummary?.level ?? "N/A"} | Trend: ${ctx.trendDirection}\n` +
    `Forecast: ${ctx.forecastNew?.toLocaleString()} (Δ ${ctx.trendDelta >= 0 ? "+" : ""}${ctx.trendDelta?.toLocaleString()})\n\n` +
    `${insight}\n\n` +
    `Ask me anything about the current planning cycle.`
  );
}

// ---------------------------------------------------------------------------
// Enhanced fallback answer engine
// ---------------------------------------------------------------------------
function buildFallbackAnswer(question: string, ctx: DashboardContext, entity?: { type: string; item: string } | null): string {
  const q = question.toLowerCase();
  const pct = ctx.totalRecords > 0 ? ((ctx.changedRecordCount / ctx.totalRecords) * 100).toFixed(1) : "0";
  const details = (ctx as any).detailRecords ?? [];

  // Entity-scoped filtering
  const entityDetails = entity ? filterDetailsByEntity(details, entity) : details;
  const entityChanged = entityDetails.filter((r: any) => r.qtyChanged || r.supplierChanged || r.designChanged || r.rojChanged);

  // Health
  if (q.includes("health") || q.includes("critical") || q.includes("score")) {
    const contrib = (ctx as any).contributionBreakdown;
    let breakdown = "";
    if (contrib) breakdown = `\n\nBreakdown: Qty ${contrib.quantity}%, Supplier ${contrib.supplier}%, Design ${contrib.design}%, Schedule ${contrib.schedule}%`;
    return `📊 Answer: Planning health is ${ctx.planningHealth}/100 (${ctx.status}).\n📈 Evidence: ${pct}% of records changed (${ctx.changedRecordCount}/${ctx.totalRecords}). Risk: ${ctx.riskSummary?.highestRiskLevel ?? "Normal"}.${breakdown}\n🎯 Scope: ${ctx.datacenterCount ?? 0} locations, ${(ctx.materialGroups ?? []).length} material groups.\n→ Action: ${(ctx.recommendedActions ?? [])[0] ?? "Review planning cycle."}`;
  }

  // Changes
  if (q.includes("changed") || q.includes("what changed") || q.includes("most")) {
    const topLoc = (ctx.datacenterSummary ?? []).sort((a, b) => b.changed - a.changed)[0];
    const topMg = (ctx.materialGroupSummary ?? []).sort((a, b) => b.changed - a.changed)[0];
    return `📊 Answer: ${ctx.changedRecordCount} records changed (${pct}%).\n📈 Evidence: Primary driver: ${ctx.drivers?.changeType ?? "N/A"}. Top location: ${topLoc?.locationId ?? "N/A"} (${topLoc?.changed ?? 0} changed). Top material group: ${topMg?.materialGroup ?? "N/A"} (${topMg?.changed ?? 0} changed).\n🎯 Scope: ${ctx.drivers?.location ?? "N/A"} is the main source.\n→ Action: ${(ctx.recommendedActions ?? [])[0] ?? "Review changes."}`;
  }

  // Forecast / demand / trend
  if (q.includes("forecast") || q.includes("demand") || q.includes("increase") || q.includes("decrease") || q.includes("trend")) {
    return `📊 Answer: Forecast is ${ctx.trendDirection} with delta of ${ctx.trendDelta >= 0 ? "+" : ""}${ctx.trendDelta?.toLocaleString()} units.\n📈 Evidence: Current: ${ctx.forecastNew?.toLocaleString()}, Previous: ${ctx.forecastOld?.toLocaleString()}.\n🎯 Scope: Affects ${ctx.changedRecordCount} records across ${ctx.datacenterCount ?? 0} locations.\n→ Action: ${ctx.trendDelta > 0 ? "Confirm capacity for increased demand." : "Review downward trend for inventory adjustment."}`;
  }

  // Location
  if (q.includes("location") || q.includes("datacenter") || q.includes("site")) {
    const topLocs = (ctx.datacenterSummary ?? []).sort((a, b) => b.changed - a.changed).slice(0, 3);
    const locList = topLocs.map(d => `${d.locationId}: ${d.changed}/${d.total} changed`).join("\n  ");
    return `📊 Answer: ${ctx.datacenterCount ?? 0} locations in scope.\n📈 Evidence:\n  ${locList || "N/A"}\n🎯 Scope: Top location: ${ctx.drivers?.location ?? "N/A"}.\n→ Action: Prioritize review for highest-change locations.`;
  }

  // Material group
  if (q.includes("material") || q.includes("group") || q.includes("category") || q.includes("equipment")) {
    const topMgs = (ctx.materialGroupSummary ?? []).sort((a, b) => b.changed - a.changed).slice(0, 3);
    const mgList = topMgs.map(g => `${g.materialGroup}: ${g.changed}/${g.total} (Qty:${g.qtyChanged} Design:${g.designChanged} Supplier:${g.supplierChanged})`).join("\n  ");
    return `📊 Answer: ${(ctx.materialGroups ?? []).length} material groups tracked.\n📈 Evidence:\n  ${mgList || "N/A"}\n→ Action: Focus on groups with highest design or supplier changes.`;
  }

  // Supplier
  if (q.includes("supplier") || q.includes("reliable") || q.includes("reliability")) {
    return `📊 Answer: ${ctx.supplierSummary?.changed ?? 0} supplier changes detected.\n📈 Evidence: Top supplier: ${ctx.drivers?.supplier ?? "N/A"}.\n🎯 Scope: ${ctx.riskSummary?.supplierChangedCount ?? 0} records with supplier transitions.\n→ Action: Validate supplier transition plans to avoid disruption.`;
  }

  // Risk
  if (q.includes("risk") || q.includes("high risk")) {
    const breakdown = ctx.riskSummary?.riskBreakdown ?? {};
    const riskList = Object.entries(breakdown).map(([k, v]) => `${k}: ${v}`).join(", ");
    return `📊 Answer: Risk level is ${ctx.riskSummary?.level ?? "N/A"} (${ctx.riskSummary?.highestRiskLevel ?? "Normal"}).\n📈 Evidence: ${ctx.highRiskRecordCount ?? 0} high-risk records. Breakdown: ${riskList || "None"}.\n→ Action: Review high-risk records for procurement and supply impact.`;
  }

  // Design / BOD / Form Factor
  if (q.includes("design") || q.includes("bod") || q.includes("form factor")) {
    return `📊 Answer: Design status: ${ctx.designSummary?.status ?? "N/A"}.\n📈 Evidence: BOD changes: ${ctx.designSummary?.bodChangedCount ?? 0}, Form Factor changes: ${ctx.designSummary?.formFactorChangedCount ?? 0}.\n🎯 Scope: ${ctx.riskSummary?.designChangedCount ?? 0} records affected.\n→ Action: Review BOD/FF changes with engineering before procurement.`;
  }

  // Schedule / ROJ
  if (q.includes("schedule") || q.includes("roj") || q.includes("delay")) {
    return `📊 Answer: ROJ status: ${ctx.rojSummary?.status ?? "N/A"}.\n📈 Evidence: ${ctx.rojSummary?.changedCount ?? 0} schedule changes detected. ${ctx.riskSummary?.rojChangedCount ?? 0} ROJ records shifted.\n→ Action: Review ROJ date shifts with supply chain team.`;
  }

  // Actions
  if (q.includes("action") || q.includes("planner") || q.includes("do next") || q.includes("recommend")) {
    const actions = ctx.recommendedActions ?? [];
    return actions.length > 0
      ? `📊 Recommended Actions:\n${actions.map((a, i) => `${i + 1}. ${a}`).join("\n")}`
      : "No specific actions recommended at this time.";
  }

  // New demand
  if (q.includes("new demand") || q.includes("new record")) {
    return `📊 Answer: New demand detected in this cycle.\n📈 Evidence: Check records flagged as new demand in detail view.\n→ Action: Establish baseline planning parameters for new materials.`;
  }

  // Cancellation
  if (q.includes("cancel")) {
    return `📊 Answer: Cancellation trends detected.\n📈 Evidence: Check records flagged as cancelled in detail view.\n→ Action: Review cancellation impact on supply commitments.`;
  }

  // Data source / provenance
  if (q.includes("blob") || q.includes("file") || q.includes("source") || q.includes("data") || q.includes("mock")) {
    const isMock = ctx.dataMode === "mock";
    return `📊 Data Source: ${isMock ? "⚠️ Mock/testing data" : "Azure Blob Storage (production)"}.\nMode: ${ctx.dataMode}\nLast refreshed: ${ctx.lastRefreshedAt ?? "N/A"}.\n${isMock ? "→ Connect to Blob Storage for real insights." : "→ Data is blob-derived and current."}`;
  }

  // KPI summary
  if (q.includes("kpi") || q.includes("metric") || q.includes("summary")) {
    return `📊 KPI Summary:\nHealth: ${ctx.planningHealth}/100 (${ctx.status})\nChanged: ${ctx.changedRecordCount}/${ctx.totalRecords} (${pct}%)\nForecast Delta: ${ctx.trendDelta >= 0 ? "+" : ""}${ctx.trendDelta?.toLocaleString()}\nTrend: ${ctx.trendDirection}\nRisk: ${ctx.riskSummary?.level ?? "N/A"}\nLocations: ${ctx.datacenterCount ?? 0}\nMaterial Groups: ${(ctx.materialGroups ?? []).length}`;
  }

  // Default
  return `📊 ${ctx.aiInsight ?? "No insight available."}\n\n📈 Root Cause: ${ctx.rootCause ?? "N/A"}\n\n→ Actions:\n${(ctx.recommendedActions ?? []).map(a => `• ${a}`).join("\n")}`;
}

function filterDetailsByEntity(details: any[], entity: { type: string; item: string }): any[] {
  const { type, item } = entity;
  if (type === "location") return details.filter((r: any) => r.locationId === item);
  if (type === "material") return details.filter((r: any) => r.materialGroup === item);
  if (type === "supplier") return details.filter((r: any) => r.supplier === item);
  if (type === "risk") return details.filter((r: any) => r.riskLevel === item);
  return details;
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export const CopilotPanel: React.FC<CopilotPanelProps> = ({ isOpen, onClose, context, selectedEntity }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const prevOpenRef = useRef(false);
  const prevEntityRef = useRef<string | null>(null);

  useEffect(() => {
    const entityKey = selectedEntity ? `${selectedEntity.type}:${selectedEntity.item}` : null;
    if (isOpen && (!prevOpenRef.current || entityKey !== prevEntityRef.current)) {
      const greeting: ChatMessage = { role: "assistant", content: buildGreeting(context, selectedEntity), timestamp: Date.now() };
      if (prevOpenRef.current && entityKey !== prevEntityRef.current) {
        setMessages((prev) => [...prev, greeting]);
      } else {
        setMessages([greeting]);
      }
      prevEntityRef.current = entityKey;
    }
    prevOpenRef.current = isOpen;
  }, [isOpen, context, selectedEntity]);

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);
  useEffect(() => { if (isOpen) setTimeout(() => inputRef.current?.focus(), 100); }, [isOpen]);

  const sendMessage = useCallback(async (question: string) => {
    if (!question.trim() || loading) return;
    const userMsg: ChatMessage = { role: "user", content: question.trim(), timestamp: Date.now() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    const timeoutId = setTimeout(() => {
      setLoading(false);
      setInput(question.trim());
      setMessages((prev) => [...prev, { role: "assistant", content: "⏱ Request timed out. Your question has been preserved — please try again.", timestamp: Date.now() }]);
    }, 6000);

    try {
      const res = await fetchExplain({ question: question.trim(), context });
      clearTimeout(timeoutId);
      const answer = res.answer || res.aiInsight || buildFallbackAnswer(question, context, selectedEntity);
      const followUps = (res as any).followUpQuestions || buildFollowUps(question, context, selectedEntity);
      
      // Build comprehensive response with new fields
      let finalAnswer = answer;
      
      // Add supporting metrics if available
      const supportingMetrics = (res as any).supportingMetrics;
      if (supportingMetrics && answer) {
        finalAnswer = `${answer}\n\n📊 Supporting Metrics:\n• Changed: ${supportingMetrics.changedRecordCount}/${supportingMetrics.totalRecords}\n• Trend: ${supportingMetrics.trendDelta >= 0 ? "+" : ""}${supportingMetrics.trendDelta?.toLocaleString()}\n• Health: ${supportingMetrics.planningHealth}/100`;
      }
      
      // Add comparison metrics if available
      const comparisonMetrics = (res as any).comparisonMetrics;
      if (comparisonMetrics && comparisonMetrics.metrics) {
        finalAnswer += `\n\n📊 Comparison:\n${JSON.stringify(comparisonMetrics, null, 2)}`;
      }
      
      // Add supplier metrics if available
      const supplierMetrics = (res as any).supplierMetrics;
      if (supplierMetrics && supplierMetrics.suppliers) {
        finalAnswer += `\n\n🏭 Suppliers at ${supplierMetrics.location}:\n`;
        supplierMetrics.suppliers.forEach((s: any) => {
          finalAnswer += `• ${s.supplier}: ${s.affectedRecords} records, Forecast: ${s.forecastImpact >= 0 ? "+" : ""}${s.forecastImpact}, Design changes: ${s.designChanges}\n`;
        });
      }
      
      // Add record comparison if available
      const recordComparison = (res as any).recordComparison;
      if (recordComparison && recordComparison.materialId) {
        finalAnswer += `\n\n📋 Record Comparison: ${recordComparison.materialId}\n`;
        finalAnswer += `Current: Forecast ${recordComparison.current.forecast}, ROJ ${recordComparison.current.roj}\n`;
        finalAnswer += `Previous: Forecast ${recordComparison.previous.forecast}, ROJ ${recordComparison.previous.roj}\n`;
        finalAnswer += `Changes: Forecast ${recordComparison.changes.forecastDelta >= 0 ? "+" : ""}${recordComparison.changes.forecastDelta}`;
      }
      
      // Add explainability note if stale
      const expl = (res as any).explainability;
      if (expl?.isStale) {
        finalAnswer = `⚠️ Data is ${Math.round(expl.dataFreshnessMinutes / 60)}h old. Consider refreshing.\n\n${finalAnswer}`;
      }
      if (expl?.confidenceScore && expl.confidenceScore < 50) {
        finalAnswer += `\n\n⚠️ Confidence: ${expl.confidenceScore}% — limited data available.`;
      }
      
      setMessages((prev) => [...prev, { role: "assistant", content: finalAnswer, timestamp: Date.now(), followUps }]);
    } catch {
      clearTimeout(timeoutId);
      const answer = buildFallbackAnswer(question, context, selectedEntity);
      const followUps = buildFollowUps(question, context, selectedEntity);
      setMessages((prev) => [...prev, { role: "assistant", content: answer, timestamp: Date.now(), followUps }]);
    } finally {
      setLoading(false);
    }
  }, [loading, context, selectedEntity]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(input); }
  };

  if (!isOpen) return null;

  const starters = buildSmartPrompts(context, selectedEntity);

  return (
    <div className="fixed top-0 right-0 h-full w-[400px] bg-[#161b22] border-l border-[#21262d] flex flex-col z-40 shadow-2xl">
      {/* Header with context label */}
      <div className="flex flex-col border-b border-[#21262d]">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2">
            <span className="text-blue-400 text-lg">✦</span>
            <span className="text-sm font-semibold text-white">Planning Copilot</span>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white transition text-lg leading-none" aria-label="Close">×</button>
        </div>
        <div className="px-4 pb-2">
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-900/30 border border-blue-500/20 text-blue-400">
            {contextLabel(selectedEntity)}
          </span>
          {context.dataMode === "mock" && (
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-yellow-900/30 border border-yellow-500/20 text-yellow-400 ml-2">Mock Data</span>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-3 flex flex-col gap-3">
        {messages.map((msg, i) => (
          <div key={i}>
            <div className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[85%] rounded-xl px-3 py-2 text-xs whitespace-pre-wrap leading-relaxed ${
                msg.role === "user" ? "bg-blue-900/40 text-blue-100 border border-blue-500/30" : "bg-[#0d1117] text-gray-300 border border-[#21262d]"
              }`}>
                {msg.content}
              </div>
            </div>
            {/* Follow-up suggestions - one at a time */}
            {msg.role === "assistant" && msg.followUps && msg.followUps.length > 0 && (
              <div className="flex flex-col gap-1.5 mt-2 ml-1">
                {msg.followUps.slice(0, 1).map((fu, j) => (
                  <button key={j} onClick={() => sendMessage(fu)}
                    className="text-[10px] px-2 py-0.5 rounded-lg bg-gray-800 border border-gray-700 text-gray-400 hover:text-blue-400 hover:border-blue-500/30 transition text-left">
                    {fu}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-[#0d1117] border border-[#21262d] rounded-xl px-3 py-2 text-xs text-gray-400">
              <span className="animate-pulse">Thinking…</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Starter prompts */}
      {messages.length <= 1 && !loading && (
        <div className="px-4 pb-2 flex flex-wrap gap-2">
          {starters.map((prompt, i) => (
            <button key={i} onClick={() => sendMessage(prompt)}
              className="text-xs px-2 py-1 rounded-lg bg-blue-900/20 border border-blue-500/30 text-blue-400 hover:bg-blue-900/40 transition">
              {prompt}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="px-4 py-3 border-t border-[#21262d] flex gap-2 items-end">
        <textarea ref={inputRef} value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={handleKeyDown}
          placeholder="Ask about the planning data…" rows={2}
          className="flex-1 bg-[#0d1117] border border-[#21262d] rounded-lg px-3 py-2 text-xs text-gray-200 placeholder-gray-500 resize-none focus:outline-none focus:border-blue-500/50"
          disabled={loading} />
        <button onClick={() => sendMessage(input)} disabled={loading || !input.trim()}
          className="px-3 py-2 rounded-lg bg-blue-900/30 border border-blue-500/30 text-blue-400 text-xs font-medium hover:bg-blue-900/50 transition disabled:opacity-40 disabled:cursor-not-allowed">
          Send
        </button>
      </div>
    </div>
  );
};
