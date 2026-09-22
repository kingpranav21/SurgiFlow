export function LineagePage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Data lineage</h1>
        <p className="text-sm text-steel-400 mt-1 max-w-2xl">
          How hospital supply events move from Kafka through Flink into risk and transfer
          recommendations on the dashboard.
        </p>
      </div>

      <div className="grid md:grid-cols-4 gap-2 text-sm">
        {[
          { t: "1. Capture", d: "Inventory, procedures, and shipments change in Postgres or are published to Kafka." },
          { t: "2. Stream", d: "Kafka topics carry those events (producers and/or CDC)." },
          { t: "3. Compute", d: "Flink joins streams to forecast demand and flag stockout risk." },
          { t: "4. Act", d: "Transfer recommendations show on the dashboard; apply one to clear risk." },
        ].map((x) => (
          <div key={x.t} className="panel p-3">
            <div className="font-medium">{x.t}</div>
            <p className="text-xs text-steel-500 mt-1 leading-relaxed">{x.d}</p>
          </div>
        ))}
      </div>

      <div className="panel p-6 font-mono text-sm leading-8 text-steel-300 overflow-x-auto">
        <pre>{`Postgres / API producers
        │
        ▼
surgiflow.*.events  ──►  Flink  ──►  stockout_risk
                                      recommendations
                                        │
                                        ▼
                                  React dashboard`}</pre>
      </div>
    </div>
  );
}
