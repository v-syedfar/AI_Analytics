import React from "react";
import { DatacenterSummary } from "../types/dashboard";

interface Props { datacenterSummary: DatacenterSummary[]; }

export const DatacenterCard: React.FC<Props> = ({ datacenterSummary }) => (
  <div className="bg-card border border-border rounded-2xl p-6">
    <p className="text-xs uppercase tracking-widest text-gray-400 mb-4">Datacenter Summary</p>
    <div className="flex flex-col gap-3">
      {datacenterSummary.map((dc, i) => {
        const pct = dc.total > 0 ? Math.round((dc.changed / dc.total) * 100) : 0;
        const barColor = pct > 50 ? "bg-red-400" : pct > 25 ? "bg-yellow-400" : "bg-green-400";
        return (
          <div key={i}>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-white font-medium">{dc.locationId}</span>
              <span className="text-gray-400">{dc.changed}/{dc.total} changed</span>
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
