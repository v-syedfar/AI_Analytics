import React from "react";

interface Props {
  recommendedActions: string[];
  onAskCopilot?: () => void;
  onNotifyPlanner?: () => void;
  onViewDetails?: () => void;
}

export const ActionsPanel: React.FC<Props> = ({
  recommendedActions, onAskCopilot, onNotifyPlanner, onViewDetails,
}) => (
  <div className="bg-card border border-border rounded-2xl p-6">
    <p className="text-xs uppercase tracking-widest text-gray-400 mb-4">Recommended Actions</p>
    <ul className="flex flex-col gap-2 mb-6">
      {recommendedActions.map((action, i) => (
        <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
          <span className="text-blue-400 mt-0.5">→</span>
          <span>{action}</span>
        </li>
      ))}
    </ul>
    <div className="flex flex-wrap gap-3">
      <button onClick={onAskCopilot}
        className="px-4 py-2 rounded-lg bg-blue-900/20 border border-blue-500/30 text-blue-400 text-sm font-medium hover:bg-blue-900/40 transition">
        ✦ Ask Copilot
      </button>
      <button onClick={onNotifyPlanner}
        className="px-4 py-2 rounded-lg bg-yellow-900/20 border border-yellow-500/30 text-yellow-400 text-sm font-medium hover:bg-yellow-900/40 transition">
        ⚑ Notify Planner
      </button>
      <button onClick={onViewDetails}
        className="px-4 py-2 rounded-lg bg-border border border-border text-gray-300 text-sm font-medium hover:bg-gray-700 transition">
        ☰ View Details
      </button>
    </div>
  </div>
);





