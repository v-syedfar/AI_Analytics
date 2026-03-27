import React from "react";

export default function SupplierCard({ supplierSummary }) {
  if (!supplierSummary?.length) return (
    <div className="bg-card border border-border rounded-2xl p-6">
      <p className="text-xs uppercase tracking-widest text-gray-400 mb-3">Supplier Changes</p>
      <p className="text-gray-500 text-sm">No supplier changes detected.</p>
    </div>
  );

  return (
    <div className="bg-card border border-border rounded-2xl p-6">
      <p className="text-xs uppercase tracking-widest text-gray-400 mb-4">Supplier Changes</p>
      <div className="flex flex-col gap-3">
        {supplierSummary.map((s, i) => (
          <div key={i} className="flex items-start justify-between border-b border-border pb-3 last:border-0 last:pb-0">
            <div>
              <p className="text-sm font-semibold text-white">{s.supplier}</p>
              {s.previousSupplier && s.previousSupplier !== s.supplier && (
                <p className="text-xs text-gray-500">from {s.previousSupplier}</p>
              )}
              <p className="text-xs text-gray-500 mt-1">{s.affectedMaterials?.length} material(s) affected</p>
            </div>
            <RiskBadge level={s.riskLevel} />
          </div>
        ))}
      </div>
    </div>
  );
}

function RiskBadge({ level }) {
  const map = {
    "Design + Supplier Change Risk": "bg-red-900/40 text-accent-red",
    "Design Change Risk": "bg-orange-900/40 text-orange-400",
    "Supplier Change Risk": "bg-yellow-900/40 text-accent-yellow",
    "High Demand Spike": "bg-purple-900/40 text-accent-purple",
    Normal: "bg-green-900/20 text-accent-green",
  };
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${map[level] || "bg-gray-800 text-gray-400"}`}>
      {level}
    </span>
  );
}
