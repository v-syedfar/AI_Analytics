import React from "react";

export default function ActionsPanel({ recommendedActions, onAskCopilot, onNotifyPlanner, onViewDetails }) {
  return (
    <div className="bg-card border border-border rounded-2xl p-6">
      <p className="text-xs uppercase tracking-widest text-gray-400 mb-4">Recommended Actions</p>
      <ul className="flex flex-col gap-2 mb-6">
        {(recommendedActions || []).map((action, i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
            <span className="text-accent-blue mt-0.5">→</span>
            <span>{action}</span>
          </li>
        ))}
      </ul>
      <div className="flex flex-wrap gap-3">
        <button
          onClick={onAskCopilot}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent-blue/10 border border-accent-blue/30 text-accent-blue text-sm font-medium hover:bg-accent-blue/20 transition"
        >
          ✦ Ask Copilot
        </button>
        <button
          onClick={onNotifyPlanner}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-yellow-900/20 border border-accent-yellow/30 text-accent-yellow text-sm font-medium hover:bg-yellow-900/40 transition"
        >
          ⚑ Notify Planner
        </button>
        <button
          onClick={onViewDetails}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-border border border-border text-gray-300 text-sm font-medium hover:bg-gray-700 transition"
        >
          ☰ View Details
        </button>
      </div>
    </div>
  );
}
