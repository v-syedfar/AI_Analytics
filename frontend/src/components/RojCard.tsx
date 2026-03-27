import React from "react";
import { RojDetail } from "../types/dashboard";

interface Props { rojSummary: { status: string; changedCount: number; details: RojDetail[] }; }

export const RojCard: React.FC<Props> = ({ rojSummary }) => (
  <div className="bg-card border border-border rounded-2xl p-6">
    <p className="text-xs uppercase tracking-widest text-gray-400 mb-4">ROJ / Schedule Changes</p>
    {!rojSummary.details.length
      ? <p className="text-gray-500 text-sm">No schedule changes detected.</p>
      : rojSummary.details.map((r, i) => (
        <div key={i} className="border-b border-gray-800 pb-3 last:border-0 last:pb-0 mb-3">
          <div className="flex justify-between">
            <p className="text-sm font-semibold text-white">{r.materialId}</p>
            <p className="text-xs text-gray-500">{r.locationId}</p>
          </div>
          <div className="flex items-center gap-2 mt-1 text-xs text-gray-400">
            <span>{r.rojPrevious}</span>
            <span className="text-yellow-400">→</span>
            <span className="text-white">{r.rojCurrent}</span>
          </div>
          {r.rojReasonCode && <p className="text-xs text-blue-400 mt-1">{r.rojReasonCode}</p>}
        </div>
      ))
    }
  </div>
);
