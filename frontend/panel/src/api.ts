export async function fetchClosed(limit = 200): Promise<any[]> {
  const url = `/events?event_type=POSITION_CLOSED&limit=${limit}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`events fetch failed: ${res.status}`);
  return await res.json();
}

export async function fetchEvents(types: string, limit = 500): Promise<any[]> {
  const url = `/events?event_type=${encodeURIComponent(types)}&limit=${limit}`;
  const r = await fetch(url);
  if (!r.ok) throw new Error(`fetch ${types} failed`);
  return await r.json();
}

export async function getRiskPolicy() {
  const r = await fetch("/risk/policy");
  if (!r.ok) throw new Error("policy get failed");
  return r.json();
}

export async function setRiskPolicy(name: string, apiKey?: string) {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (apiKey) headers["X-API-Key"] = apiKey;
  const r = await fetch("/risk/policy", {
    method: "PUT",
    headers,
    body: JSON.stringify({ name }),
  });
  if (!r.ok) throw new Error("policy put failed");
  return r.json();
}

export async function getDexQuote(params: {
  sell: string;
  buy: string;
  amount: number;
  chain?: string;
}) {
  const q = new URLSearchParams({
    sell: params.sell,
    buy: params.buy,
    amount: String(params.amount),
    ...(params.chain ? { chain: params.chain } : {}),
  });
  const r = await fetch(`/dex/quote?${q.toString()}`);
  if (!r.ok) throw new Error("dex quote failed");
  return r.json();
}

export async function getNftFloor(collection: string) {
  const r = await fetch(
    `/nft/floor?collection=${encodeURIComponent(collection)}`
  );
  if (!r.ok) throw new Error("nft floor failed");
  return r.json();
}

export async function getNftSnipePlan(
  collection: string,
  budget: number,
  discountPct: number
) {
  const q = new URLSearchParams({
    collection,
    budget_usd: String(budget),
    discount_pct: String(discountPct),
  });
  const r = await fetch(`/nft/snipe/plan?${q.toString()}`);
  if (!r.ok) throw new Error("nft snipe failed");
  return r.json();
}

export async function getL2Yields() {
  const r = await fetch(`/l2/yields`);
  if (!r.ok) throw new Error("l2 yields failed");
  return r.json();
}

export async function getDexQuoteSeries(
  sell = "ETH",
  buy = "USDC",
  points = 20
) {
  const out: { t: number; p: number | null }[] = [];
  for (let i = 0; i < points; i++) {
    const r = await fetch(`/dex/quote?sell=${sell}&buy=${buy}&amount=0.1`);
    const j = await r.json();
    out.push({ t: Date.now(), p: j.price || null });
    await new Promise((resolve) => setTimeout(resolve, 150));
  }
  return out;
}

export async function getAlertsHistory(params: {
  severity?: string;
  source?: string;
  days?: number;
  limit?: number;
  q?: string;
}): Promise<AlertItem[]> {
  const u = new URL("/alerts/history", window.location.origin);
  if (params.severity && params.severity !== "all")
    u.searchParams.set("severity", params.severity);
  if (params.source && params.source !== "all")
    u.searchParams.set("source", params.source);
  u.searchParams.set("days", String(params.days ?? 3));
  u.searchParams.set("limit", String(params.limit ?? 300));
  if (params.q && params.q.trim()) u.searchParams.set("q", params.q.trim());
  const r = await fetch(u.toString(), { credentials: "include" });
  if (!r.ok) throw new Error("alerts/history failed");
  return (await r.json()) as AlertItem[];
}

export async function triggerTestAlert(
  payload?: Partial<AlertItem> & { targets?: string[] }
) {
  const r = await fetch("/alerts/trigger", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title: payload?.title ?? "Test Alert",
      severity: payload?.severity ?? "info",
      source: payload?.source ?? "custom",
      details: payload?.details ?? { note: "panel test" },
      targets: payload?.targets ?? [],
    }),
  });
  if (!r.ok) throw new Error("trigger alert failed");
  return r.json();
}

export async function fetchEventsTimeline(
  f: EventFilter = {}
): Promise<TimelineEvent[]> {
  const p = new URLSearchParams();
  if (f.event_type) p.set("event_type", f.event_type);
  if (f.symbol) p.set("symbol", f.symbol);
  if (f.trace_id) p.set("trace_id", f.trace_id);
  if (f.since_iso) p.set("since_iso", f.since_iso);
  if (f.q) p.set("q", f.q);
  p.set("limit", String(f.limit ?? 800));
  const r = await fetch(`/events?${p.toString()}`);
  if (!r.ok) throw new Error(`events ${r.status}`);
  return (await r.json()) as TimelineEvent[];
}

export async function getEventStats(params?: {
  days?: number;
  since_iso?: string;
  event_type?: string;
}) {
  const q = new URLSearchParams();
  if (params?.days) q.set("days", String(params.days));
  if (params?.since_iso) q.set("since_iso", params.since_iso);
  if (params?.event_type) q.set("event_type", params.event_type);
  const res = await fetch(`/analytics/stats?` + q.toString());
  if (!res.ok) throw new Error("stats failed");
  return (await res.json()) as EventStats;
}

export async function getEventTimeseries(params?: {
  interval?: "1m" | "5m" | "15m" | "1h";
  days?: number;
  since_iso?: string;
  event_type?: string;
}) {
  const q = new URLSearchParams();
  q.set("interval", params?.interval ?? "5m");
  if (params?.days) q.set("days", String(params.days));
  if (params?.since_iso) q.set("since_iso", params.since_iso);
  if (params?.event_type) q.set("event_type", params.event_type);
  const res = await fetch(`/analytics/timeseries?` + q.toString());
  if (!res.ok) throw new Error("timeseries failed");
  return (await res.json()) as TimeSeries;
}

export async function getTopTraces(params?: {
  days?: number;
  since_iso?: string;
  limit?: number;
}) {
  const q = new URLSearchParams();
  if (params?.days) q.set("days", String(params.days));
  if (params?.since_iso) q.set("since_iso", params.since_iso);
  if (params?.limit) q.set("limit", String(params.limit));
  const res = await fetch(`/analytics/traces?` + q.toString());
  if (!res.ok) throw new Error("traces failed");
  return (await res.json()) as TracesResp;
}

export async function askTelegramBrain(payload: TelegramAiBrainAskPayload) {
  const res = await fetch("/telegram/ai/brain/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("AI ask failed");
  return (await res.json()) as TelegramAiBrainAskResponse;
}






