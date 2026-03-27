import React from "react";

function Tile({ label, value, sub, color = "text-white" }) {
  return (
    <div className="bg-card border border-border rounded-xl p-4 flex flex-col gap-1">
      <p className="text-xs text-gray-500 uppercase tracking-wider">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
      {sub && <p className="text-xs text-gray-500">{sub}</p>}
    </div>
  );
}

export default function SummaryTiles({ data }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      <Tile label="Total Records" value={data.totalRecords} />
      <Tile label="Changed" value={data.changedRecordCount} color="text-accent-yellow" sub={`${Math.round(data.changedRecordCount / data.totalRecords * 100)}% of total`} />
      <Tile label="Unchanged" value={data.unchangedRecordCount} color="text-accent-green" />
      <Tile label="New Records" value={data.newRecordCount} color="text-accent-blue" sub="No prior baseline" />
    </div>
  );
}
