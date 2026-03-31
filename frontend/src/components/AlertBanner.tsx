import React from "react";
import { AlertPayload } from "../types/dashboard";

const severityStyle: Record<string, string> = {
  critical: "bg-red-950/60 border-red-500/50 text-red-300",
  high: "bg-orange-950/60 border-orange-500/50 text-orange-300",
  warning: "bg-yellow-950/60 border-yellow-500/50 text-yellow-300",
  info: "bg-blue-950/60 border-blue-500/50 text-blue-300",
};

const severityIcon: Record<string, string> = {
  critical: "🔴",
  high: "🟠",
  warning: "🟡",
  info: "🔵",
};

interface Props {
  alert: AlertPayload;
}

export const AlertBanner: React.FC<Props> = ({ alert }) => {
  if (!alert.shouldTrigger) return null;

  const style = severityStyle[alert.severity] || severityStyle.info;
  const icon = severityIcon[alert.severity] || "ℹ️";

  return (
    <div className={`border rounded-xl px-4 py-3 flex items-start gap-3 ${style}`}>
      <span className="text-lg mt-0.5">{icon}</span>
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="text-xs uppercase tracking-widest font-semibold opacity-70">
            {alert.severity} alert
          </span>
          <span className="text-xs opacity-50">· {alert.triggerType}</span>
        </div>
        <p className="text-sm mt-0.5">{alert.message}</p>
        {alert.recommendedAction && (
          <p className="text-xs mt-1 opacity-70">→ {alert.recommendedAction}</p>
        )}
      </div>
    </div>
  );
};





