import React from "react";

export default function MaterialGroupCard({ materialGroupSummary }) {
  return (
    <div className="bg-card border border-border rounded-2xl p-6">
      <p className="text-xs uppercase tracking-widest text-gray-400 mb-4">Material Group Trends</p>
      <div className="flex flex-col gap-3">
        {(materialGroupSummary || []).map((mg, i) => (
          <div key={i} className="border-b border-border pb-3 last:border-0 last:pb-0">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-white font-medium">{mg.materialGroup}</span>
              <span className="text-gray-400">{mg.changed}/{mg.total}</span>
            </div>
            <div className="flex gap-3 text-xs text-gray-500">
              {mg.qtyChanged > 0 && <span className="text-accent-blue">Qty: {mg.qtyChanged}</span>}
              {mg.designChanged > 0 && <span className="text-orange-400">Design: {mg.designChanged}</span>}
              {mg.supplierChanged > 0 && <span className="text-accent-yellow">Supplier: {mg.supplierChanged}</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
