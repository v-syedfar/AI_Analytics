import React from "react";
import { DatacenterSummary } from "../types/dashboard";

interface Props {
  datacenterSummary: DatacenterSummary[];
  onLocationClick?: (locationId: string) => void;
}

export const DatacenterCard: React.FC<Props> = ({ datacenterSummary, onLocationClick }) => {
  const sorted = [...datacenterSummary].sort((a, b) => {
    const pctA = a.total > 0 ? a.changed / a.total : 0;
    const pctB = b.total > 0 ? b.changed / b.total : 0;
    return pctB - pctA;
  });

  return (
    <div className="bg-card border border-border rounded-2xl p-6">
      <p className="text-xs uppercase tracking-widest text-gray-400 mb-4">Datacenter Summary</p>
      <div className="flex flex-col gap-3">
        {sorted.map((dc, i) => {
          const pct = dc.total > 0 ? Math.round((dc.changed / dc.total) * 100) : 0;
          const barColor = pct > 50 ? "bg-red-400" : pct > 25 ? "bg-yellow-400" : "bg-green-400";
          return (
            <div
              key={i}
              className={`${onLocationClick ? "cursor-pointer hover:bg-white/5 -mx-2 px-2 py-1 rounded-lg transition" : ""}`}
              onClick={() => onLocationClick?.(dc.locationId)}
            >
              <div className="flex justify-between text-sm mb-1">
                <span className={`font-medium ${onLocationClick ? "text-blue-400 hover:underline" : "text-white"}`}>{dc.locationId}</span>
                <span className="text-gray-400">{dc.changed}/{dc.total} ({pct}%)</span>
              </div>
              <div className="w-full bg-gray-800 rounded-full h-1.5">
                <div className={`h-1.5 rounded-full ${barColor}`} style={{ width: `${pct}%` }} />
              </div>
              {dc.dcSite && <p className="text-xs text-gray-500 mt-0.5">{dc.dcSite}</p>}
            </div>
          );
        })}
      </div>
    </div>
  );
};
