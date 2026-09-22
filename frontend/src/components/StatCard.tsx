export function RiskBadge({ level }: { level: string }) {
  const l = level.toUpperCase();
  const cls =
    l === "HIGH"
      ? "bg-signal-high/15 text-signal-high border-signal-high/30"
      : l === "MEDIUM"
        ? "bg-signal-med/15 text-signal-med border-signal-med/30"
        : "bg-signal-low/15 text-signal-low border-signal-low/30";
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded border text-xs font-mono ${cls}`}>
      {l}
    </span>
  );
}

export function StatCard({
  label,
  value,
  hint,
  tone = "default",
}: {
  label: string;
  value: string | number;
  hint?: string;
  tone?: "default" | "danger" | "ok";
}) {
  const valueCls =
    tone === "danger" ? "text-signal-high" : tone === "ok" ? "text-signal-low" : "text-steel-100";
  return (
    <div className="panel p-4">
      <div className="label">{label}</div>
      <div className={`mt-2 text-3xl font-semibold tracking-tight ${valueCls}`}>{value}</div>
      {hint ? <div className="mt-1 text-xs text-steel-500">{hint}</div> : null}
    </div>
  );
}
