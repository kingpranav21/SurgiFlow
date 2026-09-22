import type {
  DashboardSummary,
  DemoSpotlight,
  EventItem,
  Forecast,
  Recommendation,
  Risk,
  SimulateResult,
} from "../types";

const BASE = import.meta.env.VITE_API_URL || "";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${res.status} ${path}`);
  return res.json();
}

async function post<T>(path: string, body: unknown = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `${res.status} ${path}`);
  }
  return res.json();
}

export const api = {
  summary: () => get<DashboardSummary>("/api/dashboard/summary"),
  spotlight: () => get<DemoSpotlight>("/api/dashboard/spotlight"),
  risks: (level?: string) => get<Risk[]>(`/api/risks${level ? `?level=${level}` : ""}`),
  recommendations: () => get<Recommendation[]>("/api/recommendations"),
  events: (limit = 40) => get<EventItem[]>(`/api/events?limit=${limit}`),
  forecast: (h: string, p: string) => get<Forecast>(`/api/forecasts/${h}/${p}`),
  simulateDelay: (delay_hours: number, shipment_id = "SHP182") =>
    post<SimulateResult>("/api/simulate/shipment-delay", { delay_hours, shipment_id }),
  applyTransfer: (recommendation_id: number) =>
    post<Recommendation>("/api/recommendations/apply", { recommendation_id }),
  recompute: () => post<{ status: string }>("/api/risks/recompute", {}),
  resetDemo: () => post<{ status: string; message: string }>("/api/demo/reset", {}),
};
