import { useEffect, useMemo, useState } from "react";
import {
    CartesianGrid, Legend, ResponsiveContainer,
    Scatter,
    ScatterChart,
    Tooltip,
    XAxis, YAxis
} from "recharts";
import { EventFilter, fetchEventsTimeline } from "../api";
import { makeWsClient } from "../lib/ws";

const EVENT_COLORS: Record<string, string> = {
  SIGNAL_INGEST: "#a0aec0",
  SIGNAL_SCORED: "#4299e1",
  AUTO_ROUTE_EXECUTED: "#38a169",
  AUTO_ROUTE_DRYRUN: "#d69e2e",
  ORDER_NEW: "#805ad5",
  ORDER_PARTIAL_FILL: "#9f7aea",
  ORDER_FILLED: "#553c9a",
  RISK_SLTP: "#ed8936",
  POSITION_CLOSED: "#e53e3e",
  DEX_QUOTE: "#319795",
  MEV_TRI: "#2b6cb0",
  MEV_ARB_OPP: "#2b6cb0",
  NFT_FLOOR: "#dd6b20",
  ALERT_SENT: "#f56565",
  TELEGRAM_REP_REFRESH: "#718096",
};

const QUICK = [
  { label: "24h", hours: 24 },
  { label: "7d", hours: 24 * 7 },
  { label: "30d", hours: 24 * 30 },
];

const ALL_TYPES = Object.keys(EVENT_COLORS);

type Row = {
  x: number;           // ms
  y: number;           // band index
  type: string;
  symbol?: string;
  trace?: string;
  payload?: any;
};

export default function EventsTimeline() {
  const [types, setTypes] = useState<string[]>(["SIGNAL_SCORED","AUTO_ROUTE_EXECUTED","POSITION_CLOSED"]);
  const [symbol, setSymbol] = useState<string>("");
  const [q, setQ] = useState<string>("");
  const [sinceHours, setSinceHours] = useState<number>(24);
  const [data, setData] = useState<Row[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [highlightTrace, setHighlightTrace] = useState<string | null>(null);
  const [live, setLive] = useState<boolean>(true);
  const [conn, setConn] = useState<'connected'|'connecting'|'disconnected'>('connecting');

  const typeBands = useMemo(() => {
    // deterministik band sırası
    const ordered = ALL_TYPES;
    const map = new Map<string, number>();
    ordered.forEach((t, i) => map.set(t, i));
    return map;
  }, []);

  const sinceISO = useMemo(() => {
    const d = new Date(Date.now() - sinceHours * 3600 * 1000);
    return d.toISOString();
  }, [sinceHours]);

  async function load() {
    setLoading(true); setError("");
    const filter: EventFilter = {
      event_type: types.join(","),
      symbol: symbol || undefined,
      q: q || undefined,
      since_iso: sinceISO,
      limit: 1000,
    };
    try {
      const events = await fetchEventsTimeline(filter);
      const rows: Row[] = events.map(e => ({
        x: new Date(e.ts).getTime(),
        y: typeBands.get(e.event_type) ?? -1,
        type: e.event_type,
        symbol: e.symbol ?? e.payload?.symbol,
        trace: e.trace_id ?? e.payload?.trace_id,
        payload: e.payload,
      })).filter(r => r.y >= 0);
      setData(rows);
    } catch (err: any) {
      setError(err?.message ?? "load failed");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); /* initial */ }, []); // eslint-disable-line
  useEffect(() => {
    // filtre değişince fetch
    const id = setTimeout(load, 250);
    return () => clearTimeout(id);
    // eslint-disable-next-line
  }, [types, symbol, q, sinceISO]);

  // Auto-refresh: 10s (fallback when WS is off)
  useEffect(() => {
    if (!live) {
      const t = setInterval(load, 10_000);
      return () => clearInterval(t);
    }
    // eslint-disable-next-line
  }, [live]);

  // PR-42: WebSocket real-time stream
  useEffect(() => {
    if (!live) {
      setConn('disconnected');
      return;
    }
    const params = new URLSearchParams();
    if (types.length) params.set("event_type", types.join(","));
    if (symbol) params.set("symbol", symbol);
    if (q) params.set("q", q);
    // not: since_iso canlı stream için tipik olarak gereksiz; sunucu yeni eventleri push'lar.

    // Determine WebSocket URL (handle port mapping)
    const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
    const host = location.hostname;
    const port = location.port === '3001' || location.port === '3000' ? '8000' : location.port;
    const url = `${protocol}://${host}:${port}/ws/events?${params}`;
    
    setConn('connecting');
    const c = makeWsClient({
      url,
      onOpen: () => setConn('connected'),
      onClose: () => setConn('disconnected'),
      onError: () => setConn('disconnected'),
      onMessage: (e) => {
        if (e?.kind === 'hello') return;
        // gelen event -> satıra dönüştür
        const r = {
          x: new Date(e.ts || Date.now()).getTime(),
          y: typeBands.get(e.event_type) ?? -1,
          type: e.event_type,
          symbol: e.symbol ?? e.payload?.symbol,
          trace: e.trace_id ?? e.payload?.trace_id,
          payload: e.payload,
        };
        if (r.y >= 0) {
          setData(curr => {
            const next = [...curr, r];
            // hafif limit: 1500
            return next.length > 1500 ? next.slice(next.length - 1500) : next;
          });
        }
      },
      reconnectDelayMs: 1000,
      maxDelayMs: 10000,
    });
    return () => c.close();
    // eslint-disable-next-line
  }, [live, types.join(','), symbol, q]);

  // trace highlight seçimi
  const highlighted = new Set<string>();
  if (highlightTrace) highlighted.add(highlightTrace);

  // rechart dataset'i: her type için ayrı Scatter (renk/legend)
  const series = ALL_TYPES.filter(t => types.includes(t)).map(t => ({
    key: t,
    color: EVENT_COLORS[t] || "#718096",
    points: data.filter(r => r.type === t),
  }));

  return (
    <div className="p-4 space-y-4 bg-white rounded-2xl shadow">
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-3">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-semibold">Event Timeline</h2>
            <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs ${
              conn==='connected'?'bg-green-100 text-green-800':conn==='connecting'?'bg-yellow-100 text-yellow-800':'bg-red-100 text-red-800'
            }`}>
              {conn}
            </span>
            <label className="inline-flex items-center gap-2 text-sm">
              <input type="checkbox" checked={live} onChange={(e)=>setLive(e.target.checked)} />
              live
            </label>
          </div>
          <p className="text-sm text-gray-500">Canlı filtrelenebilir zaman çizelgesi (WebSocket real-time + 10s fallback)</p>
        </div>
        <div className="flex flex-wrap items-end gap-2">
          <div>
            <label className="text-xs text-gray-500">Types</label>
            <select
              multiple
              value={types}
              onChange={(e) => {
                const opts = Array.from(e.target.selectedOptions).map(o => o.value);
                setTypes(opts.length ? opts : ALL_TYPES);
              }}
              className="border rounded px-2 py-1 min-w-[220px]"
            >
              {ALL_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-500">Symbol</label>
            <input value={symbol} onChange={e=>setSymbol(e.target.value)} placeholder="BTCUSDT / ETH/USDT"
              className="border rounded px-2 py-1" />
          </div>
          <div>
            <label className="text-xs text-gray-500">Search</label>
            <input value={q} onChange={e=>setQ(e.target.value)} placeholder="text search"
              className="border rounded px-2 py-1" />
          </div>
          <div className="flex items-center gap-1">
            {QUICK.map(qb => (
              <button key={qb.label}
                onClick={()=>setSinceHours(qb.hours)}
                className={`px-2 py-1 rounded border ${sinceHours===qb.hours ? 'bg-black text-white' : 'bg-gray-50'}`}>
                {qb.label}
              </button>
            ))}
          </div>
          <button onClick={load} className="px-3 py-1 rounded bg-blue-600 text-white">Refresh</button>
        </div>
      </div>

      {error && <div className="text-red-600 text-sm">{error}</div>}
      {loading && <div className="text-gray-500 text-sm">Loading…</div>}

      <div className="h-[420px]">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              type="number"
              dataKey="x"
              domain={["dataMin", "dataMax"]}
              tickFormatter={(v:number)=> new Date(v).toLocaleTimeString()}
            />
            <YAxis
              type="number"
              dataKey="y"
              tickFormatter={(yv:number)=>{
                const entry = [...typeBands.entries()].find(([_, idx])=> idx===yv);
                return entry?.[0] ?? "";
              }}
              allowDecimals={false}
              width={170}
            />
            <Tooltip
              formatter={(val:any, name:any, props:any) => {
                // props.payload = Row
                const r: Row = props?.payload;
                return [
                  r?.symbol || r?.type,
                  new Date(r.x).toLocaleString()
                ];
              }}
              contentStyle={{ fontSize: 12 }}
            />
            <Legend />
            {series.map(s => (
              <Scatter
                key={s.key}
                name={s.key}
                data={s.points}
                fill={s.color}
                onClick={(p:any) => setHighlightTrace(p?.payload?.trace ?? null)}
                shape={(props:any) => {
                  const tr = props?.payload?.trace;
                  const isHL = tr && highlighted.has(tr);
                  return (
                    <circle
                      cx={props.cx}
                      cy={props.cy}
                      r={isHL ? 6 : 4}
                      stroke={isHL ? "#111827" : "none"}
                      strokeWidth={isHL ? 2 : 0}
                      fill={props.fill}
                      style={{ cursor: "pointer", opacity: isHL ? 1 : 0.9 }}
                    />
                  );
                }}
              />
            ))}
          </ScatterChart>
        </ResponsiveContainer>
      </div>

      {highlightTrace && (
        <div className="text-sm">
          <span className="font-semibold">Trace:</span> <code>{highlightTrace}</code>
          <button onClick={()=>setHighlightTrace(null)} className="ml-2 text-blue-600 underline">clear</button>
        </div>
      )}

      {/* Mini table of last 12 rows for details */}
      <div className="mt-4">
        <h3 className="font-semibold mb-2">Recent (12)</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500">
                <th className="py-1 pr-3">Time</th>
                <th className="py-1 pr-3">Type</th>
                <th className="py-1 pr-3">Symbol</th>
                <th className="py-1 pr-3">Trace</th>
                <th className="py-1 pr-3">Details</th>
              </tr>
            </thead>
            <tbody>
              {data.slice(-12).reverse().map((r,i)=>(
                <tr key={i} className="border-t">
                  <td className="py-1 pr-3">{new Date(r.x).toLocaleString()}</td>
                  <td className="py-1 pr-3">
                    <span className="px-2 py-0.5 rounded text-white" style={{background: EVENT_COLORS[r.type] || "#4A5568"}}>
                      {r.type}
                    </span>
                  </td>
                  <td className="py-1 pr-3">{r.symbol ?? "-"}</td>
                  <td className="py-1 pr-3">
                    {r.trace ? (
                      <button className="text-blue-600 underline" onClick={()=>setHighlightTrace(r.trace!)}>{r.trace}</button>
                    ) : "—"}
                  </td>
                  <td className="py-1 pr-3">
                    <details>
                      <summary className="cursor-pointer text-blue-700">view</summary>
                      <pre className="bg-gray-50 p-2 rounded overflow-x-auto">{JSON.stringify(r.payload, null, 2)}</pre>
                    </details>
                  </td>
                </tr>
              ))}
              {data.length === 0 && (
                <tr><td colSpan={5} className="py-3 text-gray-500">No data</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

