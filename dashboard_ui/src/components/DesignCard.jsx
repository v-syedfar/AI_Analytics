import React from "react";

export default function DesignCard({ designSummary }) {
  if (!designSummary?.length) return (
    <div className="bg-card border border-border rounded-2xl p-6">
      <p className="text-xs uppercase tracking-widest text-gray-400 mb-3">Design Changes (BOD / FF)</p>
      <p className="text-gray-500 text-sm">No design changes detected.</p>
    </div>
  );

  return (
    <div className="bg-card border border-border rounded-2xl p-6">
      <p className="text-xs uppercase tracking-widest text-gray-400 mb-4">Design Changes (BOD / FF)</p>
      <div className="flex flex-col gap-3">
        {designSummary.map((d, i) => (
          <div key={i} className="border-b border-border pb-3 last:border-0 last:pb-0">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-sm font-semibold text-white">{d.materialId}</p>
                <p className="text-xs text-gray-500">{d.locationId} · {d.materialGroup}</p>
              </div>
              <span className="text-xs px-2 py-0.5 rounded-full bg-orange-900/40 text-orange-400">{d.riskLevel}</span>
            </div>
            <div className="grid grid-cols-2 gap-2 mt-2 text-xs">
              <div>
                <p className="text-gray-500">BOD</p>
                <p className="text-gray-400">{d.bodPrevious} <span className="text-accent-yellow">→</span> <span className="text-white">{d.bodCurrent}</span></p>
              </div>
              <div>
                <p className="text-gray-500">Form Factor</p>
                <p className="text-gray-400">{d.ffPrevious} <span className="text-accent-yellow">→</span> <span className="text-white">{d.ffCurrent}</span></p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
