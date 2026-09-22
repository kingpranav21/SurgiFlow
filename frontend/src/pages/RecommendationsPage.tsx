import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import type { Recommendation } from "../types";

export function RecommendationsPage() {
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [busy, setBusy] = useState<number | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  const load = () => api.recommendations().then(setRecs).catch(console.error);

  useEffect(() => {
    load();
    const id = setInterval(load, 4000);
    return () => clearInterval(id);
  }, []);

  const apply = async (id: number) => {
    setBusy(id);
    setMsg(null);
    try {
      const rec = await api.applyTransfer(id);
      setMsg(
        `Done — moved ${rec.quantity} ${rec.product_name || rec.product_id} from ${
          rec.source_hospital_name || rec.source_hospital_id
        } to ${rec.target_hospital_name || rec.target_hospital_id}. Check Overview: critical risks should drop.`
      );
      await load();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Transfer failed");
    } finally {
      setBusy(null);
    }
  };

  const pending = recs.filter((r) => r.status === "PENDING");
  const applied = recs.filter((r) => r.status === "APPLIED");

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Transfer recommendations</h1>
        <p className="text-sm text-steel-400 mt-1 max-w-2xl">
          When Flink (or the local risk engine) marks a hospital HIGH risk, SurgiFlow finds surplus at
          another site and proposes a move — plain English first, IDs second.
        </p>
      </div>
      {msg ? <div className="panel px-4 py-3 text-sm text-signal-accent leading-relaxed">{msg}</div> : null}

      {pending.length === 0 && applied.length === 0 ? (
        <div className="panel p-6 text-steel-400 text-sm space-y-2">
          <p>No transfers yet.</p>
          <p>
            Go to{" "}
            <Link to="/what-if" className="text-signal-accent hover:underline">
              What-If
            </Link>
            , delay <span className="font-mono text-steel-300">SHP182</span> by 18h, then come back
            here to apply H004 → H001.
          </p>
        </div>
      ) : null}

      <div className="grid gap-3">
        {pending.map((r) => (
          <div
            key={r.recommendation_id}
            className="panel p-4 flex flex-wrap items-center justify-between gap-4 border border-signal-accent/20"
          >
            <div className="max-w-xl">
              <div className="text-xs font-mono text-signal-accent">ACTION NEEDED</div>
              <div className="text-lg font-semibold tracking-tight mt-1">
                Transfer {r.quantity} {r.product_name || r.product_id}
              </div>
              <div className="text-sm text-steel-200 mt-1">
                From <strong>{r.source_hospital_name || r.source_hospital_id}</strong>
                {" → "}
                <strong>{r.target_hospital_name || r.target_hospital_id}</strong>
              </div>
              <p className="text-sm text-steel-400 mt-2 leading-relaxed">
                {r.plain_english || r.reason}
              </p>
              <div className="text-xs font-mono text-steel-500 mt-2">
                {r.source_hospital_id} → {r.target_hospital_id} · {r.product_id}
              </div>
            </div>
            <button
              disabled={busy === r.recommendation_id}
              onClick={() => apply(r.recommendation_id)}
              className="px-4 py-2 rounded-md bg-signal-accent text-ink-950 text-sm font-medium hover:brightness-110 disabled:opacity-50"
            >
              {busy === r.recommendation_id ? "Applying…" : "Apply transfer"}
            </button>
          </div>
        ))}

        {applied.map((r) => (
          <div key={r.recommendation_id} className="panel p-4 opacity-80">
            <div className="text-xs font-mono text-signal-low">APPLIED</div>
            <div className="text-sm font-medium mt-1">
              Moved {r.quantity} {r.product_name || r.product_id}:{" "}
              {r.source_hospital_name || r.source_hospital_id} →{" "}
              {r.target_hospital_name || r.target_hospital_id}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
