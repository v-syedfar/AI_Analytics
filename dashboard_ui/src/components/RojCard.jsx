import React from "react";

export default function RojCard({ rojSummary }) {
  if (!rojSummary?.length) return (
    <div className="bg-card border border-border rounded-2xl p-6">
      <p className="text-xs uppercase tracking-widest text-gray-400 mb-3">ROJ / Schedule Changes</p>
      <p className="text-gray-500 text-sm">No schedule changes detected.</p>
    </div>
  );

  return (
    <div className="bg-card border border-border rounded-2xl p-6">
      <p className="text-xs uppercase tracking-widest text-gray-400 mb-4">ROJ / Schedule Changes</p>
      <div className="flex flex-col gap-3">
        {rojSummary.map((r, i) => (
          <div key={i} className="border-b border-border pb-3 last:border-0 last:pb-0">
            <div className="flex justify-between">
              <p className="text-sm font-semibold text-white">{r.materialId}</p>
              <p className="text-xs text-gray-500">{r.locationId}</p>
            </div>
            <div className="flex items-center gap-2 mt-1 text-xs text-gray-400">
              <span>{r.rojPrevious}</span>
              <span className="text-accent-yellow">→</span>
              <span className="text-white">{r.rojCurrent}</span>
            </div>
            {r.rojReasonCode && (
              <p className="text-xs text-accent-blue mt-1">{r.rojReasonCode}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
