import React from "react";
import { MaterialGroupSummary } from "../types/dashboard";

interface Props {
  materialGroupSummary: MaterialGroupSummary[];
  onMaterialClick?: (materialGroup: string) => void;
}

export const MaterialGroupCard: React.FC<Props> = ({ materialGroupSummary, onMaterialClick }) => {
  const sorted = [...materialGroupSummary].sort((a, b) => b.changed - a.changed);

  return (
    <div className="bg-card border border-border rounded-2xl p-6">
      <p className="text-xs uppercase tracking-widest text-gray-400 mb-4">Material Group Trends</p>
      <div className="flex flex-col gap-3">
        {sorted.map((mg, i) => {
          const pct = mg.total > 0 ? Math.round((mg.changed / mg.total) * 100) : 0;
          const dominant = mg.qtyChanged >= mg.designChanged && mg.qtyChanged >= mg.supplierChanged ? "Qty" : mg.designChanged >= mg.supplierChanged ? "Design" : "Supplier";
          return (
            <div
              key={i}
              className={`border-b border-gray-800 pb-3 last:border-0 last:pb-0 ${onMaterialClick ? "cursor-pointer hover:bg-white/5 -mx-2 px-2 py-1 rounded-lg transition" : ""}`}
              onClick={() => onMaterialClick?.(mg.materialGroup)}
            >
              <div className="flex justify-between text-sm mb-1">
                <span className={`font-medium ${onMaterialClick ? "text-purple-400 hover:underline" : "text-white"}`}>{mg.materialGroup}</span>
                <span className="text-gray-400">{mg.changed}/{mg.total} ({pct}%)</span>
              </div>
              <div className="flex gap-3 text-xs text-gray-500">
                {mg.qtyChanged > 0 && <span className="text-blue-400">Qty: {mg.qtyChanged}</span>}
                {mg.designChanged > 0 && <span className="text-orange-400">Design: {mg.designChanged}</span>}
                {mg.supplierChanged > 0 && <span className="text-yellow-400">Supplier: {mg.supplierChanged}</span>}
                <span className="text-gray-600">Driver: {dominant}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
