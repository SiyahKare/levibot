import { useEffect, useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { EventStats, getEventStats, getEventTimeseries, getTopTraces, TimeSeries, TracesResp } from "../api";

const COLORS = ["#2563eb","#16a34a","#f59e0b","#ef4444","#7c3aed","#0891b2","#f472b6","#84cc16","#22d3ee","#fb7185"];

export default function Analytics() {
  const [days, setDays] = useState<number>(1);
  const [typesCsv, setTypesCsv] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [stats, setStats] = useState<EventStats | null>(null);
  const [series, setSeries] = useState<TimeSeries | null>(null);
  const [traces, setTraces] = useState<TracesResp | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [interval, setIntervalStr] = useState<"1m"|"5m"|"15m"|"1h">("5m");

  const refresh = async () => {
    setLoading(true);
    setError(null);
    try {
      const [s, t, r] = await Promise.all([
        getEventStats({ days, event_type: typesCsv || undefined }),
        getEventTimeseries({ interval, days, event_type: typesCsv || undefined }),
        getTopTraces({ days, limit: 20 })
      ]);
      setStats(s); setSeries(t); setTraces(r);
    } catch (e:any) {
      setError(e.message || "fetch failed");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { refresh(); /* auto-refresh */ const id = setInterval(refresh, 30000); return () => clearInterval(id); }, [days, typesCsv, interval]); // eslint-disable-line

  const pieData = useMemo(() => {
    if (!stats) return [];
    return Object.entries(stats.event_types).map(([name, value]) => ({ name, value }));
  }, [stats]);

  const symData = useMemo(() => {
    if (!stats) return [];
    const arr = Object.entries(stats.symbols).map(([symbol, count]) => ({ symbol, count }));
    arr.sort((a,b)=>b.count-a.count);
    return arr.slice(0,10);
  }, [stats]);

  return (
    <div className="p-4 bg-white rounded-2xl shadow">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Analytics Dashboard</h2>
        <div className="flex gap-2">
          <select className="border rounded px-2 py-1" value={days} onChange={e=>setDays(parseInt(e.target.value))}>
            <option value={1}>Last 24h</option>
            <option value={7}>Last 7d</option>
            <option value={30}>Last 30d</option>
          </select>
          <select className="border rounded px-2 py-1" value={interval} onChange={e=>setIntervalStr(e.target.value as any)}>
            <option value="1m">1m</option><option value="5m">5m</option><option value="15m">15m</option><option value="1h">1h</option>
          </select>
          <input className="border rounded px-2 py-1 w-64" placeholder="event_type CSV (e.g. SIGNAL_SCORED,POSITION_CLOSED)" value={typesCsv} onChange={e=>setTypesCsv(e.target.value)} />
          <button className="px-3 py-1 bg-black text-white rounded" onClick={refresh}>Refresh</button>
        </div>
      </div>

      {error && <div className="text-red-600 mb-3">Error: {error}</div>}
      {loading && <div className="text-gray-500 mb-3">Loading…</div>}

      {/* Row 1: Pie + Line */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-3 border rounded-xl">
          <h3 className="font-medium mb-2">Event Type Distribution</h3>
          <div className="h-64">
            <ResponsiveContainer>
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" outerRadius={100} label>
                  {pieData.map((_, idx) => <Cell key={idx} fill={COLORS[idx % COLORS.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="text-sm text-gray-500 mt-2">Total: {stats?.total ?? 0}</div>
        </div>

        <div className="p-3 border rounded-xl">
          <h3 className="font-medium mb-2">Events Timeline ({interval})</h3>
          <div className="h-64">
            <ResponsiveContainer>
              <LineChart data={series?.points ?? []} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="ts" tick={{ fontSize: 10 }} />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Line type="monotone" dataKey="count" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Row 2: Symbols + Traces */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
        <div className="p-3 border rounded-xl">
          <h3 className="font-medium mb-2">Top Symbols</h3>
          <div className="h-64">
            <ResponsiveContainer>
              <BarChart data={symData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="symbol" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" fill="#2563eb" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="p-3 border rounded-xl">
          <h3 className="font-medium mb-2">Top Traces</h3>
          <div className="overflow-auto max-h-64">
            <table className="w-full text-sm">
              <thead><tr className="text-left"><th className="py-1">Trace</th><th>Events</th><th>Duration</th><th>First</th><th>Last</th></tr></thead>
              <tbody>
                {(traces?.rows ?? []).map((r)=>(
                  <tr key={r.trace_id} className="border-t">
                    <td className="py-1 font-mono">{r.trace_id.slice(0,10)}</td>
                    <td>{r.event_count}</td>
                    <td>{r.duration_sec}s</td>
                    <td className="text-xs text-gray-500">{new Date(r.first_ts).toLocaleTimeString()}</td>
                    <td className="text-xs text-gray-500">{new Date(r.last_ts).toLocaleTimeString()}</td>
                  </tr>
                ))}
                {(!traces || traces.rows.length===0) && <tr><td className="py-2 text-gray-500" colSpan={5}>No traces</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

