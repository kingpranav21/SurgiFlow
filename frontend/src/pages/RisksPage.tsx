import { useEffect, useState } from "react";
import { api } from "../lib/api";
import type { Risk } from "../types";
import { RiskBadge } from "../components/StatCard";

export function RisksPage() {
  const [risks, setRisks] = useState<Risk[]>([]);
  const [filter, setFilter] = useState<"ALL" | "HIGH" | "MEDIUM" | "LOW">("ALL");

  useEffect(() => {
    const load = () => api.risks().then(setRisks).catch(console.error);
    load();
    const id = setInterval(load, 4000);
    return () => clearInterval(id);
  }, []);

  const shown = risks.filter((r) => (filter === "ALL" ? true : r.risk_level === filter));

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Inventory risk</h1>
        <p className="text-sm text-steel-400 mt-1 max-w-2xl">
          Projected stockout from joining inventory + procedure demand + shipment status. HIGH means
          surgeries may be disrupted within ~48 hours.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {(["ALL", "HIGH", "MEDIUM", "LOW"] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1 rounded-md text-xs font-mono border ${
              filter === f
                ? "border-signal-accent text-signal-accent bg-signal-accent/10"
                : "border-white/10 text-steel-500"
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      <div className="grid gap-2">
        {shown.map((r) => (
          <div key={`${r.hospital_id}-${r.product_id}`} className="panel p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <RiskBadge level={r.risk_level} />
                  <span className="font-medium">{r.product_name || r.product_id}</span>
                </div>
                <div className="text-sm text-steel-400 mt-1">
                  {r.hospital_name || r.hospital_id}
                  <span className="font-mono text-xs text-steel-500 ml-2">{r.hospital_id}</span>
                </div>
              </div>
              <div className="text-right text-xs font-mono text-steel-500">
                <div>stock {r.current_inventory}</div>
                <div>need {r.projected_demand}</div>
                <div className={r.projected_inventory < 0 ? "text-signal-high" : ""}>
                  projected {r.projected_inventory}
                </div>
              </div>
            </div>
            <p className="text-sm text-steel-300 mt-3 leading-relaxed">
              {r.plain_english || r.reason}
            </p>
            {r.reason && r.plain_english ? (
              <p className="text-xs text-steel-500 mt-1">{r.reason}</p>
            ) : null}
            {r.predicted_stockout ? (
              <p className="text-xs font-mono text-steel-500 mt-2">
                Est. stockout: {new Date(r.predicted_stockout).toLocaleString()}
              </p>
            ) : null}
          </div>
        ))}
      </div>
    </div>
  );
}
