import React from "react";
import { DashboardResponse } from "../types/dashboard";

interface TileProps { label: string; value: number | string; sub?: string; color?: string; }

const Tile: React.FC<TileProps> = ({ label, value, sub, color = "text-white" }) => (
  <div className="bg-card border border-border rounded-xl p-4 flex flex-col gap-1">
    <p className="text-xs text-gray-500 uppercase tracking-wider">{label}</p>
    <p className={`text-2xl font-bold ${color}`}>{value}</p>
    {sub && <p className="text-xs text-gray-500">{sub}</p>}
  </div>
);

interface Props { data: DashboardResponse; }

export const SummaryTiles: React.FC<Props> = ({ data }) => {
  const pct = data.totalRecords > 0
    ? Math.round((data.changedRecordCount / data.totalRecords) * 100)
    : 0;
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      <Tile label="Total Records" value={data.totalRecords} />
      <Tile label="Changed" value={data.changedRecordCount} color="text-yellow-400"
        sub={`${pct}% of total`} />
      <Tile label="Unchanged" value={data.unchangedRecordCount} color="text-green-400" />
      <Tile label="New Records" value={data.newRecordCount} color="text-blue-400"
        sub="No prior baseline" />
    </div>
  );
};





