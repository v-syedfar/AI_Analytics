import React from "react";

const riskColor: Record<string, string> = {
  "Design + Supplier Change Risk": "text-red-400",
  "Design Change Risk": "text-orange-400",
  "Supplier Change Risk": "text-yellow-400",
  "High Demand Spike": "text-purple-400",
  Normal: "text-green-400",
};

interface Props {
  riskSummary: {
    highestRiskLevel: string;
    riskBreakdown: Record<string, number>;
    highRiskCount: number;
    quantityChangedCount: number;
    supplierChangedCount: number;
    designChangedCount: number;
    rojChangedCount: number;
  };
  onRiskClick?: (riskLevel: string) => void;
}

export const RiskCard: React.FC<Props> = ({ riskSummary, onRiskClick }) => {
  const color = riskColor[riskSummary.highestRiskLevel] || "text-gray-400";
  return (
    <div className="bg-card border border-border rounded-2xl p-6">
      <p className="text-xs uppercase tracking-widest text-gray-400 mb-4">Risk Summary</p>
      <div className="flex items-center gap-3 mb-4">
        <div className={`text-3xl font-bold ${color}`}>{riskSummary.highRiskCount}</div>
        <div>
          <p className="text-sm text-white font-medium">High Risk Records</p>
          <p className={`text-xs ${color}`}>{riskSummary.highestRiskLevel}</p>
        </div>
      </div>
      <div className="flex flex-col gap-2">
        {Object.entries(riskSummary.riskBreakdown).map(([level, count]) => (
          <div
            key={level}
            className={`flex justify-between text-sm ${onRiskClick ? "cursor-pointer hover:bg-white/5 -mx-2 px-2 py-0.5 rounded transition" : ""}`}
            onClick={() => onRiskClick?.(level)}
          >
            <span className={riskColor[level] || "text-gray-400"}>{level}</span>
            <span className="text-white font-semibold">{count}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
