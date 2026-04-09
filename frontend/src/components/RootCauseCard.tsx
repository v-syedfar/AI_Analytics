import React from "react";

interface Props { rootCause: string; }

export const RootCauseCard: React.FC<Props> = ({ rootCause }) => (
  <div className="bg-card border border-border rounded-2xl p-6">
    <div className="flex items-center gap-2 mb-3">
      <span className="text-yellow-400">⚑</span>
      <p className="text-xs uppercase tracking-widest text-gray-400">Root Cause Analysis</p>
    </div>
    <p className="text-sm text-gray-300 leading-relaxed">{rootCause || "Root cause not available."}</p>
  </div>
);





