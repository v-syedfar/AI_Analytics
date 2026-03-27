import React from "react";

const directionStyle = {
  increasing: { color: "text-accent-green", bg: "bg-green-900/20", label: "Increasing ▲" },
  decreasing: { color: "text-accent-red", bg: "bg-red-900/20", label: "Decreasing ▼" },
  stable: { color: "text-accent-blue", bg: "bg-blue-900/20", label: "Stable —" },
  volatile: { color: "text-accent-yellow", bg: "bg-yellow-900/20", label: "Volatile ⚡" },
};

export default function TrendCard({ trendDirection, changeDrivers, totalRecords, changedRecordCount }) {
  const style = directionStyle[trendDirection] || directionStyle.stable;
  const pct = totalRecords > 0 ? Math.round((changedRecordCount / totalRecords) * 100) : 0;

  return (
    <div className="bg-card border border-border rounded-2xl p-6 flex flex-col gap-4">
      <p className="text-xs uppercase tracking-widest text-gray-400">Change Trend</p>
      <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-semibold w-fit ${style.bg} ${style.color}`}>
        {style.label}
      </div>
      <div className="flex justify-between text-sm mt-1">
        <span className="text-gray-400">{changedRecordCount} changed</span>
        <span className="text-gray-400">{pct}% of {totalRecords}</span>
      </div>
      <div className="w-full bg-border rounded-full h-1.5">
        <div className={`h-1.5 rounded-full ${style.color.replace("text-", "bg-")}`} style={{ width: `${pct}%` }} />
      </div>
      <div className="grid grid-cols-2 gap-2 mt-1">
        {[
          ["Quantity", changeDrivers?.quantityChangedCount],
          ["Supplier", changeDrivers?.supplierChangedCount],
          ["Design", changeDrivers?.designChangedCount],
          ["Schedule", changeDrivers?.rojChangedCount],
        ].map(([label, val]) => (
          <div key={label} className="flex justify-between text-xs text-gray-400">
            <span>{label}</span>
            <span className="text-white font-medium">{val ?? 0}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
