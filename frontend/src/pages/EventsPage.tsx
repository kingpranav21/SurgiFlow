import { useEffect, useState } from "react";
import { api } from "../lib/api";
import type { EventItem } from "../types";

export function EventsPage() {
  const [events, setEvents] = useState<EventItem[]>([]);

  useEffect(() => {
    const load = () => api.events().then(setEvents).catch(console.error);
    load();
    const id = setInterval(load, 2500);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Live event stream</h1>
        <p className="text-sm text-steel-400 mt-1 max-w-2xl">
          Every row is an operational change. With Confluent connected, the same updates become Kafka
          topics via Postgres CDC, then Flink recomputes risk.
        </p>
      </div>
      <div className="panel divide-y divide-white/5 max-h-[70vh] overflow-auto">
        {events.length === 0 ? (
          <div className="p-4 text-steel-500 text-sm">Waiting for events…</div>
        ) : (
          events.map((e) => (
            <div key={e.event_id} className="px-4 py-3 flex gap-4 items-start">
              <span className="text-steel-500 shrink-0 w-[4.5rem] font-mono text-xs pt-0.5">
                {new Date(e.event_time).toLocaleTimeString()}
              </span>
              <div className="min-w-0">
                <div className="text-sm text-steel-100">{e.message || e.event_type}</div>
                <div className="text-xs font-mono text-steel-500 mt-1 flex flex-wrap gap-x-3 gap-y-0.5">
                  <span className="text-signal-accent/80">{e.event_type}</span>
                  {e.hospital_name || e.hospital_id ? (
                    <span>{e.hospital_name || e.hospital_id}</span>
                  ) : null}
                  {e.product_name || e.product_id ? (
                    <span>{e.product_name || e.product_id}</span>
                  ) : null}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
