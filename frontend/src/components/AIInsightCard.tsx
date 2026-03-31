import React from "react";

interface Props { aiInsight: string; }

export const AIInsightCard: React.FC<Props> = ({ aiInsight }) => (
  <div className="bg-gradient-to-br from-blue-950/60 to-card border border-blue-500/30 rounded-2xl p-6">
    <div className="flex items-center gap-2 mb-3">
      <span className="text-blue-400 text-lg">✦</span>
      <p className="text-xs uppercase tracking-widest text-blue-400">AI Insight</p>
    </div>
    <p className="text-sm text-gray-200 leading-relaxed">{aiInsight || "No insight available."}</p>
  </div>
);





