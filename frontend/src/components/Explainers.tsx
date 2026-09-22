import { Link } from "react-router-dom";
import { RiskBadge } from "./StatCard";

export function StatusBanner({
  headline,
  detail,
  nextAction,
  tone,
}: {
  headline: string;
  detail: string;
  nextAction: string;
  tone: "ok" | "warn" | "danger";
}) {
  const border =
    tone === "danger"
      ? "border-signal-high/40 bg-signal-high/10"
      : tone === "warn"
        ? "border-signal-med/40 bg-signal-med/10"
        : "border-signal-low/40 bg-signal-low/10";

  return (
    <div className={`panel p-4 border ${border}`}>
      <div className="text-sm font-semibold tracking-tight">{headline}</div>
      <p className="text-sm text-steel-300 mt-1 leading-relaxed">{detail}</p>
      <p className="text-xs text-steel-500 mt-2">{nextAction}</p>
    </div>
  );
}

export function PipelineExplainer() {
  const steps = [
    { label: "Hospital data", hint: "Inventory · procedures · shipments" },
    { label: "Kafka events", hint: "CDC streams changes" },
    { label: "Flink", hint: "Forecast · risk · action" },
    { label: "Dashboard", hint: "What to do now" },
  ];
  return (
    <div className="panel p-4">
      <div className="label mb-3">How SurgiFlow works</div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        {steps.map((s, i) => (
          <div key={s.label} className="relative rounded-md bg-ink-800/80 border border-white/5 px-3 py-2">
            <div className="text-[10px] font-mono text-steel-500">0{i + 1}</div>
            <div className="text-sm font-medium mt-0.5">{s.label}</div>
            <div className="text-xs text-steel-500 mt-0.5">{s.hint}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function SpotlightCard({
  spotlight,
}: {
  spotlight: {
    hospital_name: string;
    product_name: string;
    current_stock: number;
    scheduled_procedures: number;
    procedure_type: string;
    shipment_id: string;
    shipment_status: string;
    delay_hours: number;
    supplier_name?: string;
    risk_level: string;
    projected_demand: number;
    projected_inventory: number;
    surplus_hospital_name: string;
    surplus_quantity: number;
    story: string;
    pipeline_hint: string;
  };
}) {
  return (
    <section className="panel overflow-hidden">
      <div className="px-4 py-3 border-b border-white/10 flex flex-wrap items-center justify-between gap-2">
        <div>
          <div className="label">Watch this story</div>
          <h2 className="font-medium mt-0.5">
            {spotlight.hospital_name} · {spotlight.product_name}
          </h2>
        </div>
        <RiskBadge level={spotlight.risk_level} />
      </div>
      <div className="p-4 space-y-4">
        <p className="text-sm text-steel-200 leading-relaxed">{spotlight.story}</p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
          <div>
            <div className="label">On hand</div>
            <div className="text-xl font-semibold mt-1">{spotlight.current_stock}</div>
          </div>
          <div>
            <div className="label">Procedures booked</div>
            <div className="text-xl font-semibold mt-1">{spotlight.scheduled_procedures}</div>
            <div className="text-xs text-steel-500">{spotlight.procedure_type}</div>
          </div>
          <div>
            <div className="label">Shipment {spotlight.shipment_id}</div>
            <div className="text-xl font-semibold mt-1 font-mono text-sm">
              {spotlight.shipment_status}
              {spotlight.delay_hours ? ` · +${spotlight.delay_hours}h` : ""}
            </div>
            <div className="text-xs text-steel-500">{spotlight.supplier_name}</div>
          </div>
          <div>
            <div className="label">Surplus nearby</div>
            <div className="text-xl font-semibold mt-1">{spotlight.surplus_quantity}</div>
            <div className="text-xs text-steel-500">{spotlight.surplus_hospital_name}</div>
          </div>
        </div>
        <div className="flex flex-wrap gap-2 text-xs">
          <span className="rounded border border-white/10 px-2 py-1 text-steel-400">
            Need ~{spotlight.projected_demand} in 48h
          </span>
          <span
            className={`rounded border px-2 py-1 ${
              spotlight.projected_inventory < 0
                ? "border-signal-high/30 text-signal-high"
                : "border-white/10 text-steel-400"
            }`}
          >
            Projected inventory: {spotlight.projected_inventory}
          </span>
        </div>
        <div className="flex flex-wrap items-center justify-between gap-3 pt-1 border-t border-white/5">
          <div className="text-xs text-steel-500 font-mono">{spotlight.pipeline_hint}</div>
          <Link
            to="/what-if"
            className="text-sm text-signal-accent hover:underline whitespace-nowrap"
          >
            Simulate a delay →
          </Link>
        </div>
      </div>
    </section>
  );
}
