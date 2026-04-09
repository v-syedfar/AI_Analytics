import React from "react";
import { DashboardContext } from "../types/dashboard";
import { DrillDownType } from "./DrillDownPanel";

interface Props {
  context: DashboardContext;
  onSelect: (type: DrillDownType, item: string) => void;
}

interface RiskRow {
  location: string;
  materialGroup: string;
  supplier: string;
  changeType: string;
  impact: string;
  riskLevel: string;
  trend: string;
}

const riskColor: Record<string, string> = {
  "Design + Supplier Change Risk": "text-red-400",
  "Design Change Risk": "text-orange-400",
  "Supplier Change Risk": "text-yellow-400",
  "High Demand Spike": "text-purple-400",
  Normal: "text-green-400",
};

export const TopRiskTable: React.FC<Props> = ({ context: ctx, onSelect }) => {
  const rows = buildRiskRows(ctx);

  if (rows.length === 0) return null;

  return (
    <div className="bg-card border border-border rounded-2xl p-6">
      <p className="text-xs uppercase tracking-widest text-gray-400 mb-4">Top Risk Areas</p>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-gray-500 border-b border-gray-800">
              <th className="text-left py-2 pr-3">Location</th>
              <th className="text-left py-2 pr-3">Material Group</th>
              <th className="text-left py-2 pr-3">Supplier</th>
              <th className="text-left py-2 pr-3">Change Type</th>
              <th className="text-left py-2 pr-3">Impact</th>
              <th className="text-left py-2">Risk</th>
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 10).map((row, i) => (
              <tr
                key={i}
                className="border-b border-gray-800/50 hover:bg-white/5 cursor-pointer transition"
                onClick={() => onSelect("location", row.location)}
              >
                <td className="py-2 pr-3 text-blue-400 hover:underline">{row.location}</td>
                <td className="py-2 pr-3 text-gray-300">{row.materialGroup}</td>
                <td className="py-2 pr-3 text-gray-300">{row.supplier}</td>
                <td className="py-2 pr-3 text-gray-400">{row.changeType}</td>
                <td className="py-2 pr-3 text-white font-medium">{row.impact}</td>
                <td className={`py-2 ${riskColor[row.riskLevel] ?? "text-gray-400"}`}>{row.riskLevel}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

function buildRiskRows(ctx: DashboardContext): RiskRow[] {
  const details = (ctx as any).detailRecords ?? [];
  if (!details.length) {
    // Fallback: build from summary data
    return (ctx.datacenterSummary ?? [])
      .filter((dc) => dc.changed > 0)
      .sort((a, b) => b.changed - a.changed)
      .slice(0, 10)
      .map((dc) => ({
        location: dc.locationId,
        materialGroup: ctx.drivers?.materialGroup ?? "—",
        supplier: ctx.drivers?.supplier ?? "—",
        changeType: ctx.drivers?.changeType ?? "—",
        impact: `${dc.changed}/${dc.total}`,
        riskLevel: ctx.riskSummary?.highestRiskLevel ?? "Normal",
        trend: ctx.trendDirection ?? "—",
      }));
  }

  // Build from detail records — group by risk, sort highest first
  const changed = details.filter((r: any) => r.qtyChanged || r.supplierChanged || r.designChanged || r.rojChanged);
  const riskOrder = ["Design + Supplier Change Risk", "Design Change Risk", "Supplier Change Risk", "High Demand Spike", "Normal"];
  changed.sort((a: any, b: any) => riskOrder.indexOf(a.riskLevel) - riskOrder.indexOf(b.riskLevel));

  return changed.slice(0, 10).map((r: any) => ({
    location: r.locationId ?? "—",
    materialGroup: r.materialGroup ?? "—",
    supplier: r.supplier ?? "—",
    changeType: r.changeType ?? "—",
    impact: r.qtyDelta != null ? `${r.qtyDelta >= 0 ? "+" : ""}${r.qtyDelta}` : "—",
    riskLevel: r.riskLevel ?? "Normal",
    trend: ctx.trendDirection ?? "—",
  }));
}
