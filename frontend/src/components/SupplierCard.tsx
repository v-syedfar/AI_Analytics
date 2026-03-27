import React from "react";
import { SupplierDetail } from "../types/dashboard";

interface Props { supplierSummary: { changed: number; topSupplier: string | null; details: SupplierDetail[] }; }

export const SupplierCard: React.FC<Props> = ({ supplierSummary }) => (
  <div className="bg-card border border-border rounded-2xl p-6">
    <p className="text-xs uppercase tracking-widest text-gray-400 mb-4">Supplier Changes</p>
    {!supplierSummary.details.length
      ? <p className="text-gray-500 text-sm">No supplier changes detected.</p>
      : supplierSummary.details.map((s, i) => (
        <div key={i} className="border-b border-gray-800 pb-3 last:border-0 last:pb-0 mb-3">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm font-semibold text-white">{s.supplier}</p>
              {s.previousSupplier && s.previousSupplier !== s.supplier &&
                <p className="text-xs text-gray-500">from {s.previousSupplier}</p>}
              <p className="text-xs text-gray-500 mt-1">{s.affectedMaterials.length} material(s)</p>
            </div>
            <span className="text-xs px-2 py-0.5 rounded-full bg-yellow-900/30 text-yellow-400">{s.riskLevel}</span>
          </div>
        </div>
      ))
    }
  </div>
);
