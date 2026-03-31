import React from "react";
import { HealthStatus } from "../types/dashboard";

const statusColor: Record<HealthStatus, string> = {
  Healthy: "#3fb950",
  Stable: "#58a6ff",
  "At Risk": "#d29922",
  Critical: "#f85149",
};

interface Props { score: number; status: HealthStatus; }

export const PlanningHealthCard: React.FC<Props> = ({ score, status }) => {
  const color = statusColor[status] || "#58a6ff";
  const r = 54, circ = 2 * Math.PI * r;
  const dash = (score / 100) * circ;

  return (
    <div className="bg-card border border-border rounded-2xl p-6 flex flex-col items-center gap-3">
      <p className="text-xs uppercase tracking-widest text-gray-400">Planning Health</p>
      <svg width="140" height="140" viewBox="0 0 140 140">
        <circle cx="70" cy="70" r={r} fill="none" stroke="#21262d" strokeWidth="10" />
        <circle cx="70" cy="70" r={r} fill="none" stroke={color} strokeWidth="10"
          strokeDasharray={`${dash} ${circ}`} strokeLinecap="round"
          transform="rotate(-90 70 70)" />
        <text x="70" y="66" textAnchor="middle" fill={color} fontSize="28" fontWeight="700">{score}</text>
        <text x="70" y="84" textAnchor="middle" fill="#8b949e" fontSize="11">{status}</text>
      </svg>
      <div className="flex gap-4 text-xs text-gray-500">
        <span>0 Critical</span><span>60 Stable</span><span>80 Healthy</span>
      </div>
    </div>
  );
};





