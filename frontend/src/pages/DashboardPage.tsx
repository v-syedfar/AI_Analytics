import React, { useEffect, useState } from "react";
import { DashboardResponse, DashboardContext, DataMode } from "../types/dashboard";
import { fetchDashboard } from "../services/api";
import { validateDashboardResponse } from "../services/validation";
import { Tooltip, val } from "../components/Tooltip";
import { CopilotPanel } from "../components/CopilotPanel";
import { DrillDownPanel, DrillDownType } from "../components/DrillDownPanel";
import { TopRiskTable } from "../components/TopRiskTable";
import { AlertBanner } from "../components/AlertBanner";
import { PlanningHealthCard } from "../components/PlanningHealthCard";
import { ForecastCard } from "../components/ForecastCard";
import { TrendCard } from "../components/TrendCard";
import { SummaryTiles } from "../components/SummaryTiles";
import { AIInsightCard } from "../components/AIInsightCard";
import { RootCauseCard } from "../components/RootCauseCard";
import { RiskCard } from "../components/RiskCard";
import { ActionsPanel } from "../components/ActionsPanel";
import { DatacenterCard } from "../components/DatacenterCard";
import { MaterialGroupCard } from "../components/MaterialGroupCard";
import { SupplierCard } from "../components/SupplierCard";
import { DesignCard } from "../components/DesignCard";
import { RojCard } from "../components/RojCard";

const USE_MOCK = process.env.REACT_APP_USE_MOCK === "true"; // OFF by default — Blob is the source of truth
const DEBUG_MODE = process.env.REACT_APP_DEBUG_MODE === "true";

function buildDashboardContext(data: DashboardResponse): DashboardContext {
  return {
    planningHealth: data.planningHealth, status: data.status,
    forecastNew: data.forecastNew, forecastOld: data.forecastOld,
    trendDelta: data.trendDelta, trendDirection: data.trendDirection,
    changedRecordCount: data.changedRecordCount, totalRecords: data.totalRecords,
    riskSummary: data.riskSummary, aiInsight: data.aiInsight,
    rootCause: data.rootCause, recommendedActions: data.recommendedActions,
    alerts: data.alerts, drivers: data.drivers, filters: data.filters,
    dataMode: data.dataMode, lastRefreshedAt: data.lastRefreshedAt,
    // Enriched MCP fields for Copilot Q&A
    datacenterSummary: data.datacenterSummary ?? [],
    materialGroupSummary: data.materialGroupSummary ?? [],
    supplierSummary: { changed: data.supplierSummary?.changed ?? 0, topSupplier: data.supplierSummary?.topSupplier ?? null },
    designSummary: { status: data.designSummary?.status ?? "N/A", bodChangedCount: data.designSummary?.bodChangedCount ?? 0, formFactorChangedCount: data.designSummary?.formFactorChangedCount ?? 0 },
    rojSummary: { status: data.rojSummary?.status ?? "N/A", changedCount: data.rojSummary?.changedCount ?? 0 },
    datacenterCount: data.datacenterCount ?? 0,
    materialGroups: data.materialGroups ?? [],
    highRiskRecordCount: data.riskSummary?.highRiskCount ?? 0,
    // Detail records for supplier queries and analysis
    detailRecords: data.detailRecords ?? [],
  };
}

function SkeletonCard() {
  return <div className="bg-card border border-border rounded-2xl h-40 animate-pulse" />;
}

function SkeletonDashboard() {
  return (
    <main className="max-w-7xl mx-auto px-4 py-6 flex flex-col gap-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <SkeletonCard /><SkeletonCard /><SkeletonCard />
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <SkeletonCard /><SkeletonCard /><SkeletonCard /><SkeletonCard />
      </div>
      <SkeletonCard />
    </main>
  );
}

const CARD_FIELD_MAP = [
  { card: "PlanningHealthCard", fields: "planningHealth, status" },
  { card: "ForecastCard", fields: "forecastNew, forecastOld, trendDelta, trendDirection" },
  { card: "TrendCard", fields: "trendDirection, riskSummary, totalRecords, changedRecordCount" },
  { card: "SummaryTiles", fields: "totalRecords, changedRecordCount, unchangedRecordCount, newRecordCount" },
  { card: "RiskCard", fields: "riskSummary" },
  { card: "AIInsightCard", fields: "aiInsight" },
  { card: "RootCauseCard", fields: "rootCause, drivers" },
  { card: "AlertBanner", fields: "alerts" },
];

function DebugPanel({ data }: { data: DashboardResponse }) {
  const [open, setOpen] = useState(false);
  const copyJson = () => {
    try { navigator.clipboard.writeText(JSON.stringify(data, null, 2)); }
    catch { alert("Clipboard unavailable."); }
  };
  const pct = data.totalRecords > 0 ? ((data.changedRecordCount / data.totalRecords) * 100).toFixed(1) : "0";
  const riskLevel = data.riskSummary?.highestRiskLevel ?? "Normal";
  const changeRatioDeduction = Math.round((data.changedRecordCount / Math.max(data.totalRecords, 1)) * 40);
  const riskDeduction = riskLevel.includes("Design + Supplier") ? 25 : riskLevel.includes("Design") || riskLevel.includes("Supplier") ? 15 : riskLevel.includes("Spike") ? 10 : 0;
  const designDeduction = Math.min((data.riskSummary?.designChangedCount ?? 0) * 2, 10);
  const supplierDeduction = Math.min((data.riskSummary?.supplierChangedCount ?? 0) * 2, 10);
  return (
    <div className="fixed bottom-4 right-4 z-50 max-w-sm w-full">
      <button onClick={() => setOpen(v => !v)} className="w-full px-3 py-1.5 text-xs bg-yellow-900/40 border border-yellow-500/40 text-yellow-400 rounded-lg hover:bg-yellow-900/60 transition">
        {open ? "▼ Hide Debug Panel" : "▲ Debug Panel"}
      </button>
      {open && (
        <div className="mt-2 bg-[#0d1117] border border-yellow-500/30 rounded-xl p-3 text-xs text-gray-300 max-h-[70vh] overflow-y-auto flex flex-col gap-3">
          <div>
            <p className="text-yellow-400 font-semibold mb-1">Raw Response Fields</p>
            <pre className="text-gray-400 text-[10px] whitespace-pre-wrap break-all">{JSON.stringify({ planningHealth: data.planningHealth, forecastNew: data.forecastNew, forecastOld: data.forecastOld, trendDelta: data.trendDelta, trendDirection: data.trendDirection, changedRecordCount: data.changedRecordCount, totalRecords: data.totalRecords, riskSummary: data.riskSummary, dataMode: data.dataMode, lastRefreshedAt: data.lastRefreshedAt }, null, 2)}</pre>
          </div>
          <div>
            <p className="text-yellow-400 font-semibold mb-1">Card → Field Mapping</p>
            <table className="w-full text-[10px]"><thead><tr className="text-gray-500"><th className="text-left pr-2">Card</th><th className="text-left">Fields</th></tr></thead>
              <tbody>{CARD_FIELD_MAP.map(r => (<tr key={r.card} className="border-t border-white/5"><td className="pr-2 py-0.5 text-blue-400">{r.card}</td><td className="text-gray-400">{r.fields}</td></tr>))}</tbody>
            </table>
          </div>
          <div>
            <p className="text-yellow-400 font-semibold mb-1">Calculation Trace</p>
            <div className="text-[10px] text-gray-400 flex flex-col gap-0.5">
              <span>Changed %: {pct}% ({data.changedRecordCount}/{data.totalRecords})</span>
              <span>HealthScore start: 100</span>
              <span>− Change ratio: -{changeRatioDeduction} (max 40)</span>
              <span>− Risk level: -{riskDeduction} ({riskLevel})</span>
              <span>− Design penalty: -{designDeduction} (max 10)</span>
              <span>− Supplier penalty: -{supplierDeduction} (max 10)</span>
              <span className="text-yellow-300 font-semibold">= Health Score: {data.planningHealth}</span>
            </div>
          </div>
          <button onClick={copyJson} className="px-2 py-1 text-[10px] bg-blue-900/30 border border-blue-500/30 text-blue-400 rounded hover:bg-blue-900/50 transition">Copy Full JSON</button>
        </div>
      )}
    </div>
  );
}

function HealthTooltip({ data }: { data: DashboardResponse }) {
  const pct = data.totalRecords > 0 ? ((data.changedRecordCount / data.totalRecords) * 100).toFixed(1) : "0";
  const band = data.planningHealth >= 80 ? "Healthy (≥80)" : data.planningHealth >= 60 ? "Stable (60–79)" : data.planningHealth >= 40 ? "At Risk (40–59)" : "Critical (<40)";
  const dominant = (data.riskSummary?.designChangedCount ?? 0) > (data.riskSummary?.supplierChangedCount ?? 0) ? "Design changes" : (data.riskSummary?.supplierChangedCount ?? 0) > 0 ? "Supplier changes" : "Change volume";
  return (
    <div className="flex flex-col gap-1">
      <p className="font-semibold text-white">Planning Health: {val(data.planningHealth)}/100</p>
      <p className="text-gray-400">Band: {band}</p>
      <p>Changed: {pct}% ({val(data.changedRecordCount)}/{val(data.totalRecords)})</p>
      <p>Highest risk: {val(data.riskSummary?.highestRiskLevel)}</p>
      <p>Design changes: {val(data.riskSummary?.designChangedCount)}</p>
      <p>Supplier changes: {val(data.riskSummary?.supplierChangedCount)}</p>
      <p className="text-yellow-400">Dominant factor: {dominant}</p>
    </div>
  );
}

function ForecastTooltip({ data }: { data: DashboardResponse }) {
  return (
    <div className="flex flex-col gap-1">
      <p className="font-semibold text-white">Forecast Details</p>
      <p>Current: {val(data.forecastNew?.toLocaleString())}</p>
      <p>Previous: {val(data.forecastOld?.toLocaleString())}</p>
      <p>Delta: {(data.trendDelta ?? 0) >= 0 ? "+" : ""}{val(data.trendDelta?.toLocaleString())}</p>
      <p>Trend: {val(data.trendDirection)}</p>
    </div>
  );
}

function RiskTooltip({ data }: { data: DashboardResponse }) {
  const breakdown = data.riskSummary?.riskBreakdown ?? {};
  return (
    <div className="flex flex-col gap-1">
      <p className="font-semibold text-white">Risk Summary</p>
      <p>Level: {val(data.riskSummary?.level)}</p>
      <p>Highest: {val(data.riskSummary?.highestRiskLevel)}</p>
      <p>High-risk records: {val(data.riskSummary?.highRiskCount)}</p>
      {Object.entries(breakdown).map(([k, v]) => <p key={k} className="text-gray-400">{k}: {v}</p>)}
    </div>
  );
}

function AIInsightTooltip({ data }: { data: DashboardResponse }) {
  const signals: string[] = [];
  if (data.drivers?.location) signals.push(`Location: ${data.drivers.location}`);
  if (data.drivers?.supplier) signals.push(`Supplier: ${data.drivers.supplier}`);
  if (data.drivers?.materialGroup) signals.push(`Material group: ${data.drivers.materialGroup}`);
  if (data.trendDirection) signals.push(`Trend: ${data.trendDirection}`);
  if (data.riskSummary?.level) signals.push(`Risk: ${data.riskSummary.level}`);
  const pct = data.totalRecords > 0 ? ((data.changedRecordCount / data.totalRecords) * 100).toFixed(1) : "0";
  signals.push(`Changed ratio: ${pct}%`);
  return (
    <div className="flex flex-col gap-1">
      <p className="font-semibold text-white">AI Insight Evidence</p>
      {signals.map((s, i) => <p key={i}>{s}</p>)}
    </div>
  );
}

function RootCauseTooltip({ data }: { data: DashboardResponse }) {
  return (
    <div className="flex flex-col gap-1">
      <p className="font-semibold text-white">Root Cause Drivers</p>
      <p>Change type: {val(data.drivers?.changeType)}</p>
      <p>Top location: {val(data.drivers?.location)}</p>
      <p>Top supplier: {val(data.drivers?.supplier)}</p>
      <p>Material group: {val(data.drivers?.materialGroup)}</p>
      <p>Trend: {val(data.trendDirection)}</p>
    </div>
  );
}

function AlertTooltip({ data }: { data: DashboardResponse }) {
  return (
    <div className="flex flex-col gap-1">
      <p className="font-semibold text-white">Alert Details</p>
      <p>Severity: {val(data.alerts?.severity)}</p>
      <p>Trigger: {val(data.alerts?.triggerType)}</p>
      <p>Action: {val(data.alerts?.recommendedAction)}</p>
    </div>
  );
}

const modeColor: Record<DataMode, string> = {
  blob: "bg-purple-900/30 text-purple-400",
  cached: "bg-blue-900/30 text-blue-400",
  mock: "bg-yellow-900/30 text-yellow-400",
};

const hoverCard = "transition-all duration-150 rounded-2xl hover:ring-1 hover:ring-[rgba(88,166,255,0.4)]";

export const DashboardPage: React.FC = () => {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copilotOpen, setCopilotOpen] = useState(false);
  const [blobFailed, setBlobFailed] = useState(false);
  const [isMockData, setIsMockData] = useState(false);
  const [drillDown, setDrillDown] = useState<{ type: DrillDownType; item: string } | null>(null);

  const openDrillDown = (type: DrillDownType, item: string) => {
    setDrillDown({ type, item });
  };
  const closeDrillDown = () => setDrillDown(null);

  const loadMockData = () => {
    import("../mock/sample_payload.json").then((m) => {
      const mockData = { ...(m.default as DashboardResponse), dataMode: "mock" as DataMode };
      setData(mockData);
      setIsMockData(true);
      setBlobFailed(false);
      setError(null);
      setLoading(false);
    });
  };

  useEffect(() => {
    if (USE_MOCK) {
      loadMockData();
      return;
    }
    fetchDashboard({})
      .then((d) => { validateDashboardResponse(d); setData(d); setLoading(false); })
      .catch((err) => {
        setError(`Blob data unavailable: ${err.message}`);
        setBlobFailed(true);
        setLoading(false);
      });
  }, []);

  if (loading) return (
    <div className="min-h-screen bg-bg text-white">
      <header className="border-b border-gray-800 px-6 py-4"><div className="h-6 w-48 bg-gray-800 rounded animate-pulse" /></header>
      <SkeletonDashboard />
    </div>
  );

  if (blobFailed && !data) return (
    <div className="min-h-screen bg-bg flex items-center justify-center">
      <div className="bg-card border border-red-500/30 rounded-2xl p-8 max-w-md text-center flex flex-col gap-4">
        <p className="text-red-400 text-lg font-semibold">Blob data unavailable</p>
        <p className="text-gray-400 text-sm">{error}</p>
        <div className="flex gap-3 justify-center mt-2">
          <button onClick={() => { setLoading(true); setBlobFailed(false); setError(null); fetchDashboard({}).then((d) => { validateDashboardResponse(d); setData(d); setLoading(false); }).catch((err) => { setError(err.message); setBlobFailed(true); setLoading(false); }); }}
            className="px-4 py-2 rounded-lg bg-blue-900/30 border border-blue-500/30 text-blue-400 text-sm font-medium hover:bg-blue-900/50 transition cursor-pointer">
            Retry Blob
          </button>
          <button onClick={loadMockData}
            className="px-4 py-2 rounded-lg bg-yellow-900/30 border border-yellow-500/30 text-yellow-400 text-sm font-medium hover:bg-yellow-900/50 transition cursor-pointer">
            Load Mock Data
          </button>
        </div>
      </div>
    </div>
  );

  if (!data) return (
    <div className="min-h-screen bg-bg flex items-center justify-center">
      <p className="text-gray-500">No planning data available.</p>
    </div>
  );

  if (data.totalRecords === 0) return (
    <div className="min-h-screen bg-bg flex items-center justify-center">
      <p className="text-gray-400 text-sm">No planning records available for the selected filters.</p>
    </div>
  );

  const context = buildDashboardContext(data);
  const timestamp = data.lastRefreshedAt ? new Date(data.lastRefreshedAt).toLocaleString() : "Refresh pending";

  return (
    <div className="min-h-screen bg-bg text-white">
      <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <svg width="24" height="24" viewBox="0 0 23 23" xmlns="http://www.w3.org/2000/svg">
            <rect x="0" y="0" width="11" height="11" fill="#f25022"/>
            <rect x="12" y="0" width="11" height="11" fill="#7fba00"/>
            <rect x="0" y="12" width="11" height="11" fill="#00a4ef"/>
            <rect x="12" y="12" width="11" height="11" fill="#ffb900"/>
          </svg>
          <div>
            <p className="text-xs text-gray-400 font-medium tracking-wide">Microsoft</p>
            <h1 className="text-lg font-semibold">Planning Intelligence</h1>
            <p className="text-xs text-gray-500 mt-0.5">
              {data.filters?.locationId ? `Location: ${data.filters.locationId}` : "All Locations"}
              {data.filters?.materialGroup ? ` · Group: ${data.filters.materialGroup}` : ""}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className={`text-xs px-2 py-1 rounded-full font-medium ${modeColor[data.dataMode]}`}>{data.dataMode}</span>
          <span className="text-xs text-gray-500">{timestamp}</span>
        </div>
      </header>

      {error && <div className="bg-yellow-900/20 border-b border-yellow-500/30 px-6 py-2 text-xs text-yellow-400">{error}</div>}
      {isMockData && <div className="bg-yellow-900/30 border-b border-yellow-500/40 px-6 py-2 text-xs text-yellow-300 flex items-center gap-2">⚠ Viewing mock data for testing — not connected to Blob Storage</div>}
      {drillDown && (
        <div className="bg-blue-900/20 border-b border-blue-500/30 px-6 py-2 text-xs text-blue-300 flex items-center justify-between">
          <span>Viewing context: <span className="capitalize">{drillDown.type}</span> · <span className="font-semibold text-white">{drillDown.item}</span></span>
          <button onClick={closeDrillDown} className="text-gray-400 hover:text-white text-xs ml-4">✕ Clear</button>
        </div>
      )}

      <div className={`transition-all duration-300 ${copilotOpen ? "lg:pr-[400px]" : ""} ${drillDown ? "lg:pr-[420px]" : ""}`}>
        <main className="max-w-7xl mx-auto px-4 py-6 flex flex-col gap-6">

          {/* 1. TOP ACTION BAR: AI Insight + Ask Copilot */}
          {data?.aiInsight && (
            <div className="flex flex-col md:flex-row gap-4 items-start">
              <div className="flex-1">
                <Tooltip content={<AIInsightTooltip data={data} />}>
                  <div className={hoverCard}><AIInsightCard aiInsight={data.aiInsight} /></div>
                </Tooltip>
              </div>
              <button
                onClick={() => setCopilotOpen(true)}
                className={`px-4 py-3 rounded-2xl border text-sm font-medium transition cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-400 flex flex-col items-center gap-1 min-w-[120px] shrink-0 ${copilotOpen ? "bg-blue-900/40 border-blue-400 text-blue-300" : "bg-blue-900/20 border-blue-500/30 text-blue-400 hover:bg-blue-900/40"}`}
              >
                <span className="text-xl">✦</span>
                <span>Ask Copilot{drillDown ? ` about ${drillDown.item}` : ""}</span>
              </button>
            </div>
          )}

          {/* 2. KPI BAR */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Tooltip content={<HealthTooltip data={data} />}><div className={hoverCard}><PlanningHealthCard score={data.planningHealth} status={data.status} /></div></Tooltip>
            <Tooltip content={<ForecastTooltip data={data} />}><div className={hoverCard}><ForecastCard forecastNew={data.forecastNew} forecastOld={data.forecastOld} trendDelta={data.trendDelta} trendDirection={data.trendDirection} /></div></Tooltip>
            <Tooltip content={<div className="flex flex-col gap-1"><p className="font-semibold text-white">Trend & Changes</p><p>Direction: {val(data.trendDirection)}</p><p>Changed: {val(data.changedRecordCount)} of {val(data.totalRecords)}</p></div>}><div className={hoverCard}><TrendCard trendDirection={data.trendDirection} riskSummary={data.riskSummary} totalRecords={data.totalRecords} changedRecordCount={data.changedRecordCount} /></div></Tooltip>
          </div>

          <SummaryTiles data={data} />

          {/* 3. ALERTS */}
          {data.alerts?.shouldTrigger && (
            <Tooltip content={<AlertTooltip data={data} />}>
              <AlertBanner alert={data.alerts} />
            </Tooltip>
          )}

          {/* 4. TOP RISK AREAS */}
          <TopRiskTable context={context} onSelect={openDrillDown} />

          {/* 5. LOCATION + MATERIAL VIEW */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <DatacenterCard datacenterSummary={data.datacenterSummary} onLocationClick={(loc) => openDrillDown("location", loc)} />
            <MaterialGroupCard materialGroupSummary={data.materialGroupSummary} onMaterialClick={(mg) => openDrillDown("material", mg)} />
          </div>

          {/* 6. SUPPLIER + DESIGN + ROJ */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <SupplierCard supplierSummary={data.supplierSummary} onSupplierClick={(s) => openDrillDown("supplier", s)} />
            <DesignCard designSummary={data.designSummary} />
            <RojCard rojSummary={data.rojSummary} />
          </div>

          {/* 7. TREND + RISK */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Tooltip content={<RiskTooltip data={data} />}><div className={hoverCard}><RiskCard riskSummary={data.riskSummary} onRiskClick={(r) => openDrillDown("risk", r)} /></div></Tooltip>
            <Tooltip content={<RootCauseTooltip data={data} />}><div className={hoverCard}><RootCauseCard rootCause={data.rootCause} /></div></Tooltip>
          </div>

          {/* 8. ACTIONS */}
          <ActionsPanel
            recommendedActions={data.recommendedActions}
            onNotifyPlanner={() => alert("Notifying planner...")}
            onViewDetails={() => alert("Opening detail view...")}
          />

        </main>
      </div>

      {/* Panels */}
      <CopilotPanel isOpen={copilotOpen} onClose={() => setCopilotOpen(false)} context={context} selectedEntity={drillDown} />
      {drillDown && (
        <DrillDownPanel
          type={drillDown.type}
          selectedItem={drillDown.item}
          contextData={context}
          isOpen={true}
          onClose={closeDrillDown}
        />
      )}
      {DEBUG_MODE && <DebugPanel data={data} />}
    </div>
  );
};
