import React from "react";

export default function AIInsightCard({ aiInsight }) {
  return (
    <div className="bg-gradient-to-br from-blue-950/60 to-card border border-accent-blue/30 rounded-2xl p-6">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-accent-blue text-lg">✦</span>
        <p className="text-xs uppercase tracking-widest text-accent-blue">AI Insight</p>
      </div>
      <p className="text-sm text-gray-200 leading-relaxed">
        {aiInsight || "No insight available."}
      </p>
    </div>
  );
}
