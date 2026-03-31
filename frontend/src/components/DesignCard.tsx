import React from "react";
import { DesignDetail } from "../types/dashboard";

interface Props { designSummary: { status: string; bodChangedCount: number; formFactorChangedCount: number; details: DesignDetail[] }; }

export const DesignCard: React.FC<Props> = ({ designSummary }) => (
  <div className="bg-card border border-border rounded-2xl p-6">
    <p className="text-xs uppercase tracking-widest text-gray-400 mb-4">Design Changes (BOD / FF)</p>
    {!designSummary.details.length
      ? <p className="text-gray-500 text-sm">No design changes detected.</p>
      : designSummary.details.map((d, i) => (
        <div key={i} className="border-b border-gray-800 pb-3 last:border-0 last:pb-0 mb-3">
          <div className="flex justify-between">
            <p className="text-sm font-semibold text-white">{d.materialId}</p>
            <span className="text-xs text-orange-400">{d.riskLevel}</span>
          </div>
          <p className="text-xs text-gray-500">{d.locationId} · {d.materialGroup}</p>
          <div className="grid grid-cols-2 gap-2 mt-2 text-xs">
            <div>
              <p className="text-gray-500">BOD</p>
              <p className="text-gray-400">{d.bodPrevious} <span className="text-yellow-400">→</span> <span className="text-white">{d.bodCurrent}</span></p>
            </div>
            <div>
              <p className="text-gray-500">Form Factor</p>
              <p className="text-gray-400">{d.ffPrevious} <span className="text-yellow-400">→</span> <span className="text-white">{d.ffCurrent}</span></p>
            </div>
          </div>
        </div>
      ))
    }
  </div>
);





