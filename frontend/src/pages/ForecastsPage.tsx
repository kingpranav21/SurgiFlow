import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../lib/api";
import type { Forecast } from "../types";

export function ForecastsPage() {
  const [hospitalId, setHospitalId] = useState("H001");
  const [productId, setProductId] = useState("STAPLER-01");
  const [fc, setFc] = useState<Forecast | null>(null);

  useEffect(() => {
    api.forecast(hospitalId, productId).then(setFc).catch(console.error);
  }, [hospitalId, productId]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Demand forecast</h1>
          <p className="text-sm text-steel-400 mt-1 max-w-xl">
            Blue = remaining stock if demand burns as forecast. Yellow = safety stock. Red =
            cumulative demand. Default view is the demo stapler at Mumbai Central.
          </p>
        </div>
        <div className="flex gap-2">
          <input
            className="bg-ink-800 border border-white/10 rounded px-3 py-1.5 text-sm font-mono"
            value={hospitalId}
            onChange={(e) => setHospitalId(e.target.value.toUpperCase())}
            placeholder="Hospital"
          />
          <input
            className="bg-ink-800 border border-white/10 rounded px-3 py-1.5 text-sm font-mono"
            value={productId}
            onChange={(e) => setProductId(e.target.value.toUpperCase())}
            placeholder="Product"
          />
        </div>
      </div>

      {fc ? (
        <>
          <div className="panel p-4 text-sm text-steel-300 leading-relaxed">
            Over the next {fc.window_hours} hours SurgiFlow expects{" "}
            <strong className="text-steel-100">{fc.forecasted_demand} units</strong> of demand (
            {fc.procedure_demand} from scheduled procedures + {fc.baseline_consumption} baseline
            consumption). Current stock is{" "}
            <strong className="text-steel-100">{fc.current_inventory}</strong>; projected ending
            inventory is{" "}
            <strong className={fc.projected_inventory < 0 ? "text-signal-high" : "text-steel-100"}>
              {fc.projected_inventory}
            </strong>
            .
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="panel p-3">
              <div className="label">Current stock</div>
              <div className="text-2xl mt-1">{fc.current_inventory}</div>
            </div>
            <div className="panel p-3">
              <div className="label">Forecast demand</div>
              <div className="text-2xl mt-1">{fc.forecasted_demand}</div>
            </div>
            <div className="panel p-3">
              <div className="label">Procedure demand</div>
              <div className="text-2xl mt-1">{fc.procedure_demand}</div>
            </div>
            <div className="panel p-3">
              <div className="label">Projected inventory</div>
              <div
                className={`text-2xl mt-1 ${fc.projected_inventory < 0 ? "text-signal-high" : ""}`}
              >
                {fc.projected_inventory}
              </div>
            </div>
          </div>

          <div className="panel p-4 h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={fc.series}>
                <CartesianGrid stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="hour" stroke="#6b7c99" tick={{ fontSize: 11 }} />
                <YAxis stroke="#6b7c99" tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ background: "#111a2b", border: "1px solid rgba(255,255,255,0.1)" }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="inventory"
                  name="Inventory"
                  stroke="#3d8bfd"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="safety_stock"
                  name="Safety stock"
                  stroke="#d4a017"
                  strokeDasharray="4 4"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="demand_cumulative"
                  name="Demand (cum.)"
                  stroke="#e35d5d"
                  strokeWidth={1.5}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      ) : (
        <div className="text-steel-500">Loading forecast…</div>
      )}
    </div>
  );
}
