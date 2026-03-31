import React from "react";
import { TrendDirection } from "../types/dashboard";

interface Props {
  forecastNew: number;
  forecastOld: number;
  trendDelta: number;
  trendDirection: TrendDirection;
}

export const ForecastCard: React.FC<Props> = ({ forecastNew, forecastOld, trendDelta, trendDirection }) => {
  const isUp = trendDelta > 0;
  const color = isUp ? "text-green-400" : trendDelta < 0 ? "text-red-400" : "text-gray-400";
  const arrow = isUp ? "▲" : trendDelta < 0 ? "▼" : "—";

  return (
    <div className="bg-card border border-border rounded-2xl p-6 flex flex-col gap-4">
      <p className="text-xs uppercase tracking-widest text-gray-400">Forecast</p>
      <div className="flex justify-between items-end">
        <div>
          <p className="text-3xl font-bold text-white">{forecastNew.toLocaleString()}</p>
          <p className="text-xs text-gray-500 mt-1">Current Qty</p>
        </div>
        <div className="text-right">
          <p className="text-lg text-gray-400">{forecastOld.toLocaleString()}</p>
          <p className="text-xs text-gray-500 mt-1">Previous</p>
        </div>
      </div>
      <div className={`flex items-center gap-2 text-sm font-semibold ${color}`}>
        <span>{arrow}</span>
        <span>{Math.abs(trendDelta).toLocaleString()} units</span>
        <span className="text-gray-500 font-normal">({trendDirection})</span>
      </div>
    </div>
  );
};





