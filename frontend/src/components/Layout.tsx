import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Overview" },
  { to: "/events", label: "Live Events" },
  { to: "/risks", label: "Inventory Risk" },
  { to: "/forecasts", label: "Forecasts" },
  { to: "/recommendations", label: "Recommendations" },
  { to: "/what-if", label: "What-If" },
  { to: "/lineage", label: "Data Lineage" },
];

type PipelineStatus = {
  pipeline_mode: string;
  kafka_enabled: boolean;
  hint: string;
};

export function Layout({ children }: { children: React.ReactNode }) {
  const [pipe, setPipe] = useState<PipelineStatus | null>(null);

  useEffect(() => {
    const base = import.meta.env.VITE_API_URL || "";
    fetch(`${base}/api/pipeline/status`)
      .then((r) => r.json())
      .then(setPipe)
      .catch(() => setPipe(null));
  }, []);

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-white/10 bg-ink-950/80 backdrop-blur sticky top-0 z-20">
        <div className="mx-auto max-w-7xl px-4 py-3 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-md bg-signal-accent/20 border border-signal-accent/40 flex items-center justify-center font-mono text-sm text-signal-accent">
              SF
            </div>
            <div>
              <div className="font-semibold tracking-tight text-steel-100">SurgiFlow</div>
              <div className="text-[11px] text-steel-500 tracking-wide">
                Real-Time Surgical Supply Chain Intelligence
              </div>
            </div>
          </div>
          <div className="hidden md:flex items-center gap-3 text-[11px] font-mono">
            {pipe ? (
              <span
                className={`inline-flex items-center gap-1.5 px-2 py-1 rounded border ${
                  pipe.kafka_enabled
                    ? "border-signal-low/40 text-signal-low"
                    : "border-steel-500/40 text-steel-500"
                }`}
                title={pipe.hint}
              >
                <span
                  className={`inline-block h-1.5 w-1.5 rounded-full ${
                    pipe.kafka_enabled ? "bg-signal-low animate-pulse" : "bg-steel-500"
                  }`}
                />
                {pipe.kafka_enabled ? `KAFKA · ${pipe.pipeline_mode}` : `LOCAL · ${pipe.pipeline_mode}`}
              </span>
            ) : (
              <span className="text-steel-500 inline-flex items-center gap-2">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-signal-low animate-pulse" />
                STREAMING OPS
              </span>
            )}
          </div>
        </div>
        <nav className="mx-auto max-w-7xl px-4 pb-2 flex gap-1 overflow-x-auto">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === "/"}
              className={({ isActive }) =>
                `px-3 py-1.5 rounded-md text-sm whitespace-nowrap transition-colors ${
                  isActive
                    ? "bg-white/10 text-steel-100"
                    : "text-steel-400 hover:text-steel-100 hover:bg-white/5"
                }`
              }
            >
              {l.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="flex-1 mx-auto max-w-7xl w-full px-4 py-6">{children}</main>
    </div>
  );
}
