import React, { useEffect, useState } from "react";
import { DashboardResponse, DataMode } from "../types/dashboard";
import { fetchDashboard } from "../services/api";

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

const USE_MOCK = process.env.REACT_APP_USE_MOCK !== "false";

export const DashboardPage: React.FC = () => {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (USE_MOCK) {
      import("../mock/sample_payload.json").then(m => {
        setData(m.default as DashboardResponse);
        setLoading(false);
      });
      return;
    }
    fetchDashboard({ mode: "cached" })
      .then(d => { setData(d); setLoading(false); })
      .catch(() => {
        import("../mock/sample_payload.json").then(m => {
          setData(m.default as DashboardResponse);
          setLoading(false);
        });
      });
  }, []);

  if (loading) return (
    <div className="min-h-screen bg-bg flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="w-10 h-10 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
        <p className="text-gray-400 text-sm">Loading planning data...</p>
      </div>
    </div>
  );

  if (error) return (
    <div className="min-h-screen bg-bg flex items-center justify-center">
      <div className="bg-card border border-red-500/30 rounded-2xl p-8 max-w-md text-center">
        <p className="text-red-400 text-lg font-semibold mb-2">Failed to load dashboard</p>
        <p className="text-gray-400 text-sm">{error}</p>
      </div>
    </div>
  );

  if (!data) return (
    <div className="min-h-screen bg-bg flex items-center justify-center">
      <p className="text-gray-500">No planning data available.</p>
    </div>
  );

  const modeColor: Record<DataMode, string> = {
    live: "bg-green-900/30 text-green-400",
    cached: "bg-blue-900/30 text-blue-400",
    blob: "bg-purple-900/30 text-purple-400",
    sharepoint: "bg-indigo-900/30 text-indigo-400",
  };

  return (
    <div className="min-h-screen bg-bg text-white">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* Microsoft Logo */}
          <svg width="24" height="24" viewBox="0 0 23 23" xmlns="http://www.w3.org/2000/svg">
            <rect x="0" y="0" width="11" height="11" fill="#f25022"/>
            <rect x="12" y="0" width="11" height="11" fill="#7fba00"/>
            <rect x="0" y="12" width="11" height="11" fill="#00a4ef"/>
            <rect x="12" y="12" width="11" height="11" fill="#ffb900"/>
          </svg>
          <div>
            <h1 className="text-lg font-semibold">Planning Intelligence</h1>
            <p className="text-xs text-gray-500 mt-0.5">
              {data.filters?.locationId ? `Location: ${data.filters.locationId}` : "All Locations"}
              {data.filters?.materialGroup ? ` · Group: ${data.filters.materialGroup}` : ""}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className={`text-xs px-2 py-1 rounded-full font-medium ${modeColor[data.dataMode]}`}>
            {data.dataMode}
          </span>
          <span className="text-xs text-gray-500">
            {data.lastRefreshedAt ? new Date(data.lastRefreshedAt).toLocaleString() : ""}
          </span>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6 flex flex-col gap-6">

        {/* Alert Banner */}
        {data.alerts?.shouldTrigger && <AlertBanner alert={data.alerts} />}

        {/* Row 1: Health + Forecast + Trend */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <PlanningHealthCard score={data.planningHealth} status={data.status} />
          <ForecastCard forecastNew={data.forecastNew} forecastOld={data.forecastOld}
            trendDelta={data.trendDelta} trendDirection={data.trendDirection} />
          <TrendCard trendDirection={data.trendDirection} riskSummary={data.riskSummary}
            totalRecords={data.totalRecords} changedRecordCount={data.changedRecordCount} />
        </div>

        {/* Row 2: KPI tiles */}
        <SummaryTiles data={data} />

        {/* Row 3: AI Insight */}
        <AIInsightCard aiInsight={data.aiInsight} />

        {/* Row 4: Datacenter + Material Groups */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <DatacenterCard datacenterSummary={data.datacenterSummary} />
          <MaterialGroupCard materialGroupSummary={data.materialGroupSummary} />
        </div>

        {/* Row 5: Supplier + Design + ROJ */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <SupplierCard supplierSummary={data.supplierSummary} />
          <DesignCard designSummary={data.designSummary} />
          <RojCard rojSummary={data.rojSummary} />
        </div>

        {/* Row 6: Risk + Root Cause */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <RiskCard riskSummary={data.riskSummary} />
          <RootCauseCard rootCause={data.rootCause} />
        </div>

        {/* Row 7: Actions */}
        <ActionsPanel
          recommendedActions={data.recommendedActions}
          onAskCopilot={() => alert("Opening Copilot Studio...")}
          onNotifyPlanner={() => alert("Notifying planner...")}
          onViewDetails={() => alert("Opening detail view...")}
        />

      </main>
    </div>
  );
};
