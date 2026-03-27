import React from "react";

const riskColor = {
  "Design + Supplier Change Risk": "text-accent-red",
  "Design Change Risk": "text-orange-400",
  "Supplier Change Risk": "text-accent-yellow",
  "High Demand Spike": "text-accent-purple",
  Normal: "text-accent-green",
};

export default function RiskCard({ riskSummary }) {
  const { highestRiskLevel, riskBreakdown, highRiskCount } = riskSummary || {};
  const color = riskColor[highestRiskLevel] || "text-gray-400";

  return (
    <div className="bg-card border border-border rounded-2xl p-6">
      <p className="text-xs uppercase tracking-widest text-gray-400 mb-4">Risk Summary</p>
      <div className="flex items-center gap-3 mb-4">
        <div className={`text-3xl font-bold ${color}`}>{highRiskCount}</div>
        <div>
          <p className="text-sm text-white font-medium">High Risk Records</p>
          <p className={`text-xs ${color}`}>{highestRiskLevel}</p>
        </div>
      </div>
      <div className="flex flex-col gap-2">
        {Object.entries(riskBreakdown || {}).map(([level, count]) => (
          <div key={level} className="flex justify-between items-center text-sm">
            <span className={`${riskColor[level] || "text-gray-400"}`}>{level}</span>
            <span className="text-white font-semibold">{count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
