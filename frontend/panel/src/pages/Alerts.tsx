import React, { useEffect, useMemo, useRef, useState } from "react";
import { getAlertsHistory, triggerTestAlert, type AlertItem } from "../api";

const SEVERITY_COLORS: Record<AlertItem["severity"], string> = {
  info: "bg-blue-100 text-blue-800",
  low: "bg-lime-100 text-lime-800",
  medium: "bg-yellow-100 text-yellow-800",
  high: "bg-orange-100 text-orange-900",
  critical: "bg-red-100 text-red-800",
};

const SOURCES = ["all", "signals", "risk", "exec", "custom"];
const SEVERITIES = ["all", "info", "low", "medium", "high", "critical"];

export default function Alerts() {
  const [items, setItems] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [severity, setSeverity] = useState<string>("all");
  const [source, setSource] = useState<string>("all");
  const [days, setDays] = useState<number>(3);
  const [q, setQ] = useState("");
  const [pageSize, setPageSize] = useState<number>(50);
  const [page, setPage] = useState<number>(1);
  const lastSeenRef = useRef<number>(Math.floor(Date.now() / 1000));

  const fetchNow = async () => {
    setLoading(true);
    try {
      const data = await getAlertsHistory({ severity, source, days, limit: 300, q });
      // en yeni üste
      data.sort((a, b) => b.ts - a.ts);
      setItems(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNow();
    // 5sn poll
    const t = setInterval(fetchNow, 5000);
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [severity, source, days, q]);

  const unread = useMemo(() => items.filter((x) => x.ts > lastSeenRef.current).length, [items]);

  const pageCount = Math.max(1, Math.ceil(items.length / pageSize));
  const pageItems = items.slice((page - 1) * pageSize, page * pageSize);

  const onSeen = () => {
    lastSeenRef.current = Math.floor(Date.now() / 1000);
  };

  const showTestBtn = import.meta.env.VITE_SHOW_TEST_ALERT === "true";

  return (
    <div className="rounded-2xl shadow p-4 bg-white dark:bg-zinc-900">
      <div className="flex items-center justify-between mb-3">
        <div className="text-xl font-semibold">Alerts</div>
        <div className="flex items-center gap-2">
          <span
            className={`inline-flex items-center px-2 py-1 rounded-full text-xs ${unread ? "bg-emerald-100 text-emerald-800" : "bg-gray-100 text-gray-600"}`}
            title="Unread since last view"
          >
            {unread} new
          </span>
          <button className="text-sm underline" onClick={onSeen}>
            mark seen
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-2 mb-3">
        <select value={severity} onChange={(e) => setSeverity(e.target.value)} className="border rounded px-2 py-1">
          {SEVERITIES.map((s) => (
            <option key={s} value={s}>
              Severity: {s}
            </option>
          ))}
        </select>
        <select value={source} onChange={(e) => setSource(e.target.value)} className="border rounded px-2 py-1">
          {SOURCES.map((s) => (
            <option key={s} value={s}>
              Source: {s}
            </option>
          ))}
        </select>
        <select value={String(days)} onChange={(e) => setDays(parseInt(e.target.value))} className="border rounded px-2 py-1">
          {[1, 3, 7].map((d) => (
            <option key={d} value={d}>
              Days: {d}
            </option>
          ))}
        </select>
        <input
          placeholder="Search title/details…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="border rounded px-2 py-1 md:col-span-2"
        />
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between mb-2">
        <div className="text-sm text-gray-500">{loading ? "Loading…" : `Total ${items.length}`}</div>
        <div className="flex items-center gap-2">
          <select value={String(pageSize)} onChange={(e) => setPageSize(parseInt(e.target.value))} className="border rounded px-2 py-1">
            {[25, 50, 100, 200].map((n) => (
              <option key={n} value={n}>
                Page size: {n}
              </option>
            ))}
          </select>
          <button onClick={fetchNow} className="border rounded px-2 py-1">
            Refresh
          </button>
          {showTestBtn && (
            <button
              onClick={() =>
                triggerTestAlert({
                  title: "Panel Test Alert",
                  severity: "info",
                  source: "custom",
                  details: { by: "panel", t: new Date().toISOString() },
                }).then(fetchNow)
              }
              className="border rounded px-2 py-1"
              title="Visible only when VITE_SHOW_TEST_ALERT=true"
            >
              Send Test
            </button>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="text-left border-b">
            <tr>
              <th className="py-2 pr-3">Time</th>
              <th className="py-2 pr-3">Title</th>
              <th className="py-2 pr-3">Severity</th>
              <th className="py-2 pr-3">Source</th>
              <th className="py-2 pr-3">Details</th>
            </tr>
          </thead>
          <tbody>
            {pageItems.map((a) => {
              const t = new Date(a.ts * 1000);
              return (
                <tr key={`${a.ts}-${a.title}`} className="border-b hover:bg-zinc-50 dark:hover:bg-zinc-800/30">
                  <td className="py-2 pr-3 whitespace-nowrap">{t.toLocaleString()}</td>
                  <td className="py-2 pr-3">{a.title}</td>
                  <td className="py-2 pr-3">
                    <span className={`px-2 py-1 rounded-full text-xs ${SEVERITY_COLORS[a.severity]}`}>{a.severity}</span>
                  </td>
                  <td className="py-2 pr-3">{a.source ?? "-"}</td>
                  <td className="py-2 pr-3 max-w-[420px]">
                    <pre className="whitespace-pre-wrap break-words text-xs text-gray-600 dark:text-gray-300">
                      {a.details ? JSON.stringify(a.details).slice(0, 400) : "-"}
                    </pre>
                  </td>
                </tr>
              );
            })}
            {!pageItems.length && (
              <tr>
                <td colSpan={5} className="py-6 text-center text-gray-500">
                  No alerts yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between mt-3">
        <div className="text-xs text-gray-500">
          Page {page}/{pageCount}
        </div>
        <div className="flex gap-2">
          <button disabled={page <= 1} onClick={() => setPage((p) => Math.max(1, p - 1))} className="border rounded px-2 py-1 disabled:opacity-40">
            Prev
          </button>
          <button
            disabled={page >= pageCount}
            onClick={() => setPage((p) => Math.min(pageCount, p + 1))}
            className="border rounded px-2 py-1 disabled:opacity-40"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}