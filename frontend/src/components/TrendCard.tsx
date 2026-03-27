import React from "react";
import { TrendDirection } from "../types/dashboard";

const dirStyle: Record<TrendDirection, { color: string; bg: string; label: string }> = {
  Increase: { color: "text-green-400", bg: "bg-green-900/20", label: "Increasing ▲" },
  Decrease: { color: "text-red-400", bg: "bg-red-900/20", label: "Decreasing ▼" },
  Stable: { color: "text-blue-400", bg: "bg-blue-900/20", label: "Stable —" },
  Volatile: { color: "text-yellow-400", bg: "bg-yellow-900/20", label: "Volatile ⚡" },
};

interface Props {
  trendDirection: TrendDirection;
  riskSummary: { quantityChangedCount: number; supplierChangedCount: number; designChangedCount: number; rojChangedCount: number; };
  totalRecords: number;
  changedRecordCount: number;
}

export const TrendCard: React.FC<Props> = ({ trendDirection, riskSummary, totalRecords, changedRecordCount }) => {
  const style = dirStyle[trendDirection] || dirStyle.Stable;
  const pct = totalRecords > 0 ? Math.round((changedRecordCount / totalRecords) * 100) : 0;

  return (
    <div className="bg-card border border-border rounded-2xl p-6 flex flex-col gap-4">
      <p className="text-xs uppercase tracking-widest text-gray-400">Change Trend</p>
      <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-semibold w-fit ${style.bg} ${style.color}`}>
        {style.label}
      </div>
      <div className="flex justify-between text-sm">
        <span className="text-gray-400">{changedRecordCount} changed</span>
        <span className="text-gray-400">{pct}% of {totalRecords}</span>
      </div>
      <div className="w-full bg-gray-800 rounded-full h-1.5">
        <div className={`h-1.5 rounded-full ${style.color.replace("text-", "bg-")}`} style={{ width: `${pct}%` }} />
      </div>
      <div className="grid grid-cols-2 gap-2">
        {[["Quantity", riskSummary.quantityChangedCount], ["Supplier", riskSummary.supplierChangedCount],
          ["Design", riskSummary.designChangedCount], ["Schedule", riskSummary.rojChangedCount]
        ].map(([label, val]) => (
          <div key={label as string} className="flex justify-between text-xs text-gray-400">
            <span>{label}</span>
            <span className="text-white font-medium">{val}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
