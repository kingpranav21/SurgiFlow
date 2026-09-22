import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import type { SimulateResult } from "../types";
import { RiskBadge } from "../components/StatCard";

const DELAYS = [4, 12, 18, 24, 48];

const STEPS = [
  {
    n: "1",
    title: "Start healthy",
    body: "Mumbai Central has 9 staplers and an on-time shipment. Critical risks should be 0.",
  },
  {
    n: "2",
    title: "Delay the shipment",
    body: "Pick 18h and simulate. SurgiFlow drops delayed inbound supply from the forecast.",
  },
  {
    n: "3",
    title: "See the risk",
    body: "H001 Endoscopic Stapler goes HIGH — procedures still need stock tomorrow.",
  },
  {
    n: "4",
    title: "Apply the transfer",
    body: "Move surplus from Mumbai West (H004) to protect the surgeries.",
  },
];

export function WhatIfPage() {
  const [delay, setDelay] = useState(18);
  const [loading, setLoading] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [result, setResult] = useState<SimulateResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  const run = async () => {
    setLoading(true);
    setError(null);
    setInfo(null);
    try {
      const res = await api.simulateDelay(delay);
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Simulation failed");
    } finally {
      setLoading(false);
    }
  };

  const reset = async () => {
    setResetting(true);
    setError(null);
    try {
      const res = await api.resetDemo();
      setResult(null);
      setInfo(res.message);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Reset failed");
    } finally {
      setResetting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">What-If simulator</h1>
        <p className="text-sm text-steel-400 mt-1 max-w-2xl">
          This is the demo heart of SurgiFlow. You inject one supplier delay; the streaming rules
          recalculate demand, risk, and a transfer recommendation.
        </p>
      </div>

      <div className="grid md:grid-cols-4 gap-2">
        {STEPS.map((s) => (
          <div key={s.n} className="panel p-3">
            <div className="text-[10px] font-mono text-steel-500">STEP {s.n}</div>
            <div className="text-sm font-medium mt-1">{s.title}</div>
            <p className="text-xs text-steel-500 mt-1 leading-relaxed">{s.body}</p>
          </div>
        ))}
      </div>

      <div className="panel p-5 space-y-4">
        <div>
          <div className="label">Shipment under test</div>
          <div className="mt-1 text-sm">
            <span className="font-mono text-signal-accent">SHP182</span>
            <span className="text-steel-400"> · Endoscopic Stapler → Mumbai Central Surgical (H001)</span>
          </div>
        </div>
        <div className="label">How many hours late?</div>
        <div className="flex flex-wrap gap-2">
          {DELAYS.map((d) => (
            <button
              key={d}
              onClick={() => setDelay(d)}
              className={`px-3 py-1.5 rounded-md text-sm font-mono border transition-colors ${
                delay === d
                  ? "bg-signal-accent/20 border-signal-accent text-signal-accent"
                  : "border-white/10 text-steel-400 hover:border-white/25"
              }`}
            >
              {d}h
              {d === 18 ? " · demo" : ""}
            </button>
          ))}
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={run}
            disabled={loading}
            className="px-5 py-2.5 rounded-md bg-signal-high/90 text-white text-sm font-semibold tracking-wide hover:brightness-110 disabled:opacity-50"
          >
            {loading ? "Simulating…" : "SIMULATE DELAY"}
          </button>
          <button
            onClick={reset}
            disabled={resetting}
            className="px-4 py-2.5 rounded-md border border-white/15 text-sm text-steel-300 hover:bg-white/5 disabled:opacity-50"
          >
            {resetting ? "Resetting…" : "Reset demo (back to healthy)"}
          </button>
        </div>
        {error ? <div className="text-signal-high text-sm">{error}</div> : null}
        {info ? <div className="text-signal-low text-sm">{info}</div> : null}
      </div>

      {result ? (
        <div className="space-y-4">
          <div className="panel p-4 border border-signal-high/30 bg-signal-high/5">
            <div className="text-sm font-semibold">What just happened</div>
            <p className="text-sm text-steel-200 mt-1 leading-relaxed">{result.explanation}</p>
            <p className="text-xs text-signal-accent mt-2">{result.next_step}</p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="panel p-4">
              <div className="label">Critical before</div>
              <div className="text-3xl mt-1">{result.critical_risks_before}</div>
            </div>
            <div className="panel p-4">
              <div className="label">Critical after</div>
              <div className="text-3xl mt-1 text-signal-high">{result.critical_risks_after}</div>
            </div>
            <div className="panel p-4">
              <div className="label">Delay applied</div>
              <div className="text-3xl mt-1 font-mono">{result.delay_hours}h</div>
            </div>
            <div className="panel p-4">
              <div className="label">Shipment</div>
              <div className="text-xl mt-1 font-mono">{result.shipment_id}</div>
              <div className="text-xs text-steel-500">{result.status}</div>
            </div>
          </div>

          <div className="panel overflow-hidden">
            <div className="px-4 py-3 border-b border-white/10 font-medium">Triggered risks</div>
            <div className="divide-y divide-white/5">
              {result.risks.length === 0 ? (
                <div className="p-4 text-steel-500 text-sm">No HIGH risks after this delay.</div>
              ) : (
                result.risks.map((r) => (
                  <div key={`${r.hospital_id}-${r.product_id}`} className="px-4 py-3 flex gap-4 items-start">
                    <RiskBadge level={r.risk_level} />
                    <div>
                      <div className="font-medium">
                        {r.product_name || r.product_id}
                        <span className="text-steel-500 font-normal">
                          {" "}
                          · {r.hospital_name || r.hospital_id}
                        </span>
                      </div>
                      <div className="text-sm text-steel-300 mt-0.5">{r.plain_english || r.reason}</div>
                      <div className="text-xs font-mono text-steel-500 mt-1">
                        stock {r.current_inventory} · demand {r.projected_demand} · projected{" "}
                        {r.projected_inventory}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="panel overflow-hidden">
            <div className="px-4 py-3 border-b border-white/10 flex items-center justify-between">
              <span className="font-medium">Recommended action</span>
              <Link to="/recommendations" className="text-sm text-signal-accent hover:underline">
                Open Recommendations →
              </Link>
            </div>
            {result.recommendations.length === 0 ? (
              <div className="p-4 text-steel-500 text-sm">No transfer recommendations.</div>
            ) : (
              result.recommendations.map((r) => (
                <div key={r.recommendation_id} className="px-4 py-3 border-b border-white/5">
                  <div className="font-semibold">
                    TRANSFER {r.quantity} {r.product_name || r.product_id}
                  </div>
                  <div className="text-sm text-signal-accent mt-0.5">
                    {r.source_hospital_name || r.source_hospital_id} →{" "}
                    {r.target_hospital_name || r.target_hospital_id}
                  </div>
                  <div className="text-sm text-steel-400 mt-1">{r.plain_english || r.reason}</div>
                </div>
              ))
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
