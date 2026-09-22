import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import type { DashboardSummary, DemoSpotlight, Risk } from "../types";
import { RiskBadge, StatCard } from "../components/StatCard";
import { PipelineExplainer, SpotlightCard, StatusBanner } from "../components/Explainers";

export function OverviewPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [spotlight, setSpotlight] = useState<DemoSpotlight | null>(null);
  const [risks, setRisks] = useState<Risk[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      const [s, r, sp] = await Promise.all([api.summary(), api.risks(), api.spotlight()]);
      setSummary(s);
      setSpotlight(sp);
      setRisks(r.filter((x) => x.risk_level !== "LOW").slice(0, 6));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    }
  };

  useEffect(() => {
    load();
    const id = setInterval(load, 4000);
    return () => clearInterval(id);
  }, []);

  if (error) {
    return (
      <div className="panel p-6 text-signal-high space-y-2">
        <div className="font-medium">Cannot reach the SurgiFlow API</div>
        <p className="text-sm text-steel-300">
          Start Postgres and the backend, then run{" "}
          <code className="text-steel-100">python scripts/seed_database.py</code>.
        </p>
        <p className="text-xs text-steel-500">{error}</p>
      </div>
    );
  }

  if (!summary || !spotlight) return <div className="text-steel-500">Loading ops board…</div>;

  const tone =
    summary.critical_risks > 0 ? "danger" : summary.delayed_shipments > 0 ? "warn" : "ok";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Network overview</h1>
        <p className="text-steel-400 text-sm mt-1">
          SurgiFlow watches inventory, scheduled surgeries, and shipments — then tells you what will go
          wrong before it does.
        </p>
      </div>

      <StatusBanner
        headline={summary.status_headline}
        detail={summary.status_detail}
        nextAction={summary.next_action}
        tone={tone}
      />

      <PipelineExplainer />

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Hospitals" value={summary.hospitals} hint="Synthetic demo network" />
        <StatCard label="Products" value={summary.products} hint="Surgical SKUs tracked" />
        <StatCard label="Healthy coverage" value={`${summary.healthy_pct}%`} tone="ok" />
        <StatCard
          label="Critical risks"
          value={summary.critical_risks}
          tone={summary.critical_risks > 0 ? "danger" : "ok"}
          hint={summary.critical_risks === 0 ? "No stockouts projected" : "Needs a transfer"}
        />
      </div>

      <div className="grid md:grid-cols-3 gap-3">
        <StatCard label="Medium risks" value={summary.medium_risks} hint="Below safety stock" />
        <StatCard
          label="Pending transfers"
          value={summary.pending_recommendations}
          hint="Recommended moves waiting"
        />
        <StatCard label="Delayed shipments" value={summary.delayed_shipments} />
      </div>

      <SpotlightCard spotlight={spotlight} />

      <section className="panel overflow-hidden">
        <div className="px-4 py-3 border-b border-white/10 flex items-center justify-between">
          <div>
            <h2 className="font-medium">Active risk board</h2>
            <p className="text-xs text-steel-500 mt-0.5">Elevated risks only — LOW coverage is hidden</p>
          </div>
          <Link to="/what-if" className="text-sm text-signal-accent hover:underline">
            Run What-If →
          </Link>
        </div>
        {risks.length === 0 ? (
          <div className="p-6 text-steel-400 text-sm space-y-2">
            <p>No elevated risks right now. The network looks healthy.</p>
            <p>
              Next: open{" "}
              <Link to="/what-if" className="text-signal-accent hover:underline">
                What-If
              </Link>{" "}
              and delay shipment <span className="font-mono text-steel-300">SHP182</span> by 18 hours.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-white/5">
            {risks.map((r) => (
              <div key={`${r.hospital_id}-${r.product_id}`} className="px-4 py-3 flex gap-4 items-start">
                <RiskBadge level={r.risk_level} />
                <div className="min-w-0 flex-1">
                  <div className="font-medium text-sm">
                    {r.product_name || r.product_id}
                    <span className="text-steel-500 font-normal"> · {r.hospital_name || r.hospital_id}</span>
                  </div>
                  <p className="text-sm text-steel-300 mt-0.5">{r.plain_english || r.reason}</p>
                  <div className="text-xs font-mono text-steel-500 mt-1">
                    stock {r.current_inventory} · need {r.projected_demand} · projected{" "}
                    <span className={r.projected_inventory < 0 ? "text-signal-high" : ""}>
                      {r.projected_inventory}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
