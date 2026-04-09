import React, { useRef, useEffect } from "react";
import { DashboardContext } from "../types/dashboard";

export type DrillDownType = "location" | "material" | "supplier" | "risk";

interface DrillDownPanelProps {
  type: DrillDownType;
  selectedItem: string;
  contextData: DashboardContext;
  isOpen: boolean;
  onClose: () => void;
}

const typeLabel: Record<DrillDownType, string> = {
  location: "Location", material: "Material Group", supplier: "Supplier", risk: "Risk Category",
};
const typeBadgeColor: Record<DrillDownType, string> = {
  location: "bg-blue-900/40 text-blue-400", material: "bg-purple-900/40 text-purple-400",
  supplier: "bg-yellow-900/40 text-yellow-400", risk: "bg-red-900/40 text-red-400",
};

function pct(n: number, total: number): string {
  return total > 0 ? `${((n / total) * 100).toFixed(1)}%` : "0%";
}

export const DrillDownPanel: React.FC<DrillDownPanelProps> = ({ type, selectedItem, contextData: ctx, isOpen, onClose }) => {
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;
    const handler = (e: MouseEvent | TouchEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) onClose();
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  // Derive metrics from context based on type
  const details = (ctx as any).detailRecords ?? [];
  const filtered = filterByType(type, selectedItem, details, ctx);
  const total = filtered.total;
  const changed = filtered.changed;
  const breakdown = filtered.breakdown;
  const impactScope = filtered.impactScope;
  const rootCauseText = filtered.rootCause;
  const relevantActions = filterActions(ctx.recommendedActions ?? [], selectedItem);

  return (
    <div ref={panelRef} className="fixed top-0 right-0 h-full w-[420px] bg-[#0d1117] border-l border-[#21262d] flex flex-col z-40 shadow-2xl overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-[#21262d] sticky top-0 bg-[#0d1117] z-10">
        <div className="flex items-center gap-2">
          <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${typeBadgeColor[type]}`}>{typeLabel[type]}</span>
          <span className="text-sm font-semibold text-white">{selectedItem}</span>
        </div>
        <button onClick={onClose} className="text-gray-400 hover:text-white text-lg leading-none" aria-label="Close">×</button>
      </div>

      <div className="px-5 py-4 flex flex-col gap-5 text-xs">
        {/* Key Metrics */}
        <Section title="Key Metrics">
          <MetricRow label="Total Records" value={String(total)} />
          <MetricRow label="Changed Records" value={String(changed)} highlight />
          <MetricRow label="% Changed" value={pct(changed, total)} />
          <MetricRow label="Trend" value={ctx.trendDirection ?? "N/A"} />
        </Section>

        {/* Breakdown */}
        <Section title="Change Breakdown">
          {breakdown.map((b) => (
            <div key={b.label} className="flex justify-between items-center">
              <span className="text-gray-400">{b.label}</span>
              <span className="text-white font-medium">{b.count} <span className="text-gray-500">({pct(b.count, changed || 1)})</span></span>
            </div>
          ))}
          {breakdown.length === 0 && <p className="text-gray-500">No breakdown available</p>}
        </Section>

        {/* Root Cause */}
        <Section title="Root Cause">
          <p className="text-gray-300 leading-relaxed">{rootCauseText || "No root cause data available for this selection."}</p>
        </Section>

        {/* Impact Scope */}
        <Section title="Impact Scope">
          {impactScope.materials.length > 0 && <MetricRow label="Materials" value={impactScope.materials.slice(0, 5).join(", ")} />}
          {impactScope.suppliers.length > 0 && <MetricRow label="Suppliers" value={impactScope.suppliers.slice(0, 5).join(", ")} />}
          {impactScope.locations.length > 0 && <MetricRow label="Locations" value={impactScope.locations.slice(0, 5).join(", ")} />}
          {impactScope.materials.length === 0 && impactScope.suppliers.length === 0 && impactScope.locations.length === 0 && <p className="text-gray-500">No detail records available</p>}
        </Section>

        {/* Recommended Actions */}
        <Section title="Recommended Actions">
          {relevantActions.length > 0 ? relevantActions.map((a, i) => (
            <div key={i} className="flex items-start gap-2"><span className="text-blue-400 mt-0.5">→</span><span className="text-gray-300">{a}</span></div>
          )) : <p className="text-gray-500">No specific actions for this selection</p>}
        </Section>

        {/* AI Reasoning */}
        {ctx.aiInsight && (
          <Section title="AI Analysis">
            <p className="text-gray-300 leading-relaxed">{ctx.aiInsight}</p>
          </Section>
        )}
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="text-[10px] uppercase tracking-widest text-gray-500 mb-2">{title}</p>
      <div className="flex flex-col gap-1.5">{children}</div>
    </div>
  );
}

function MetricRow({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="flex justify-between">
      <span className="text-gray-400">{label}</span>
      <span className={highlight ? "text-yellow-400 font-semibold" : "text-white"}>{value}</span>
    </div>
  );
}

interface FilterResult {
  total: number; changed: number;
  breakdown: { label: string; count: number }[];
  rootCause: string;
  impactScope: { materials: string[]; suppliers: string[]; locations: string[] };
}

function filterByType(type: DrillDownType, item: string, details: any[], ctx: DashboardContext): FilterResult {
  const empty: FilterResult = { total: 0, changed: 0, breakdown: [], rootCause: "", impactScope: { materials: [], suppliers: [], locations: [] } };

  if (type === "location") {
    const dc = (ctx.datacenterSummary ?? []).find((d) => d.locationId === item);
    if (!dc) return { ...empty, rootCause: `No data found for location ${item}` };
    const locDetails = details.filter((r: any) => r.locationId === item);
    return {
      total: dc.total, changed: dc.changed,
      breakdown: buildBreakdown(locDetails),
      rootCause: buildRootCause(locDetails, ctx, item),
      impactScope: buildImpactScope(locDetails),
    };
  }

  if (type === "material") {
    const mg = (ctx.materialGroupSummary ?? []).find((g) => g.materialGroup === item);
    if (!mg) return { ...empty, rootCause: `No data found for material group ${item}` };
    const mgDetails = details.filter((r: any) => r.materialGroup === item);
    return {
      total: mg.total, changed: mg.changed,
      breakdown: [
        { label: "Quantity changes", count: mg.qtyChanged ?? 0 },
        { label: "Design changes", count: mg.designChanged ?? 0 },
        { label: "Supplier changes", count: mg.supplierChanged ?? 0 },
      ].filter((b) => b.count > 0),
      rootCause: buildRootCause(mgDetails, ctx, item),
      impactScope: buildImpactScope(mgDetails),
    };
  }

  if (type === "supplier") {
    const supDetails = details.filter((r: any) => r.supplier === item);
    const changedSup = supDetails.filter((r: any) => r.qtyChanged || r.supplierChanged || r.designChanged || r.rojChanged);
    return {
      total: supDetails.length, changed: changedSup.length,
      breakdown: buildBreakdown(changedSup),
      rootCause: `Supplier ${item} is associated with ${changedSup.length} changed record(s). ${ctx.rootCause ?? ""}`,
      impactScope: buildImpactScope(supDetails),
    };
  }

  if (type === "risk") {
    const riskDetails = details.filter((r: any) => r.riskLevel === item);
    return {
      total: riskDetails.length, changed: riskDetails.length,
      breakdown: buildBreakdown(riskDetails),
      rootCause: `${riskDetails.length} record(s) classified as ${item}. ${ctx.rootCause ?? ""}`,
      impactScope: buildImpactScope(riskDetails),
    };
  }

  return empty;
}

function buildBreakdown(records: any[]): { label: string; count: number }[] {
  if (!records.length) return [];
  const qty = records.filter((r) => r.qtyChanged).length;
  const sup = records.filter((r) => r.supplierChanged).length;
  const des = records.filter((r) => r.designChanged).length;
  const roj = records.filter((r) => r.rojChanged).length;
  return [
    { label: "Quantity changes", count: qty },
    { label: "Supplier changes", count: sup },
    { label: "Design changes", count: des },
    { label: "Schedule changes", count: roj },
  ].filter((b) => b.count > 0);
}

function buildRootCause(records: any[], ctx: DashboardContext, item: string): string {
  if (!records.length) return `No changed records found for ${item}.`;
  const changed = records.filter((r: any) => r.qtyChanged || r.supplierChanged || r.designChanged || r.rojChanged);
  const drivers: string[] = [];
  const qty = changed.filter((r: any) => r.qtyChanged).length;
  const sup = changed.filter((r: any) => r.supplierChanged).length;
  const des = changed.filter((r: any) => r.designChanged).length;
  if (qty > 0) drivers.push(`quantity (${qty})`);
  if (sup > 0) drivers.push(`supplier (${sup})`);
  if (des > 0) drivers.push(`design (${des})`);
  const primary = drivers.length > 0 ? `Primary drivers: ${drivers.join(", ")}.` : "";
  return `${changed.length} of ${records.length} records changed for ${item}. ${primary}`;
}

function buildImpactScope(records: any[]): { materials: string[]; suppliers: string[]; locations: string[] } {
  return {
    materials: Array.from(new Set(records.map((r: any) => r.materialId).filter(Boolean))),
    suppliers: Array.from(new Set(records.map((r: any) => r.supplier).filter(Boolean))),
    locations: Array.from(new Set(records.map((r: any) => r.locationId).filter(Boolean))),
  };
}

function filterActions(actions: string[], item: string): string[] {
  const itemLower = item.toLowerCase();
  const relevant = actions.filter((a) => a.toLowerCase().includes(itemLower));
  return relevant.length > 0 ? relevant : actions.slice(0, 3);
}
