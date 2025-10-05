import { useEffect, useMemo, useState } from "react";
import { fetchEvents } from "../api";
import type { EventRec } from "../types";
import { getTs } from "../types";

function normHead(s: string) {
  return (s || "").trim().toUpperCase().replace(/\s+/g, " ").slice(0, 120);
}

export default function SignalsTimeline() {
  const [scored, setScored] = useState<EventRec[]>([]);
  const [routes, setRoutes] = useState<EventRec[]>([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  // Filters
  const [label, setLabel] = useState<"all" | "BUY" | "SELL" | "NO-TRADE">("all");
  const [minConf, setMinConf] = useState(0.5);
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);

  useEffect(() => {
    let alive = true;
    const pull = async () => {
      try {
        setLoading(true);
        const [sc, rt] = await Promise.all([
          fetchEvents("SIGNAL_SCORED", 800),
          fetchEvents("AUTO_ROUTE_EXECUTED,AUTO_ROUTE_DRYRUN", 400),
        ]);
        if (!alive) return;
        setScored(Array.isArray(sc) ? sc : []);
        setRoutes(Array.isArray(rt) ? rt : []);
        setErr(null);
      } catch (e: any) {
        if (!alive) return;
        setErr(e?.message ?? "fetch error");
      } finally {
        if (alive) setLoading(false);
      }
    };
    pull();
    const id = setInterval(pull, 5000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  // index routes by (head, ~time)
  const routeIdx = useMemo(() => {
    const idx = new Map<string, EventRec[]>();
    for (const r of routes) {
      const text = r.payload?.text || "";
      const head = normHead(text);
      if (!idx.has(head)) idx.set(head, []);
      idx.get(head)!.push(r);
    }
    // keep route lists sorted by time (desc)
    for (const arr of idx.values()) {
      arr.sort((a, b) => getTs(b) - getTs(a));
    }
    return idx;
  }, [routes]);

  // decorate scored with routed flag (join by text head and |Δt|<=120s)
  const joined = useMemo(() => {
    return scored.map((s) => {
      const text = s.payload?.text || "";
      const head = normHead(text);
      const ts = getTs(s);
      let routed: null | { dryrun: boolean; at: number } = null;
      const cands = routeIdx.get(head) || [];
      for (const r of cands) {
        const dt = Math.abs(getTs(r) - ts);
        if (dt <= 120) {
          routed = { dryrun: r.event_type === "AUTO_ROUTE_DRYRUN", at: getTs(r) };
          break;
        }
      }
      return { s, routed };
    });
  }, [scored, routeIdx]);

  // apply filters
  const filtered = useMemo(() => {
    const term = q.trim().toUpperCase();
    return joined.filter(({ s }) => {
      const lab = (s.payload?.label || "").toUpperCase();
      const conf = Number(s.payload?.confidence ?? 0);
      const txt = (s.payload?.text || "").toUpperCase();
      const okLabel = label === "all" || lab === label;
      const okConf = conf >= minConf;
      const okText = term === "" || txt.includes(term);
      return okLabel && okConf && okText;
    });
  }, [joined, label, minConf, q]);

  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => getTs(b.s) - getTs(a.s));
  }, [filtered]);

  const total = sorted.length;
  const maxPage = Math.max(1, Math.ceil(total / pageSize));
  const pageSafe = Math.min(page, maxPage);
  const slice = useMemo(() => {
    const start = (pageSafe - 1) * pageSize;
    return sorted.slice(start, start + pageSize);
  }, [sorted, pageSafe, pageSize]);

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-xl font-semibold">Signals Timeline</h1>

      <div className="flex flex-wrap gap-3 items-end">
        <div className="flex flex-col">
          <label className="text-sm text-gray-500">Label</label>
          <select
            className="border rounded px-2 py-1"
            value={label}
            onChange={(e) => {
              setLabel(e.target.value as any);
              setPage(1);
            }}
          >
            <option value="all">all</option>
            <option value="BUY">BUY</option>
            <option value="SELL">SELL</option>
            <option value="NO-TRADE">NO-TRADE</option>
          </select>
        </div>
        <div className="flex flex-col">
          <label className="text-sm text-gray-500">Min confidence</label>
          <div className="flex items-center gap-2">
            <input
              type="range"
              min={0}
              max={0.99}
              step={0.01}
              value={minConf}
              onChange={(e) => {
                setMinConf(parseFloat(e.target.value));
                setPage(1);
              }}
            />
            <span className="text-sm">{minConf.toFixed(2)}</span>
          </div>
        </div>
        <div className="flex flex-col grow">
          <label className="text-sm text-gray-500">Search</label>
          <input
            className="border rounded px-2 py-1"
            placeholder="text contains…"
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setPage(1);
            }}
          />
        </div>
        <div className="flex flex-col">
          <label className="text-sm text-gray-500">Page size</label>
          <select
            className="border rounded px-2 py-1"
            value={pageSize}
            onChange={(e) => {
              setPageSize(parseInt(e.target.value));
              setPage(1);
            }}
          >
            {[25, 50, 100, 200].map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </div>
        <div className="ml-auto text-sm">
          {loading ? "Loading…" : err ? <span className="text-red-600">{err}</span> : `${total} rows`}
        </div>
      </div>

      <div className="overflow-auto border rounded">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="p-2 text-left w-[160px]">Time</th>
              <th className="p-2 text-left">Text</th>
              <th className="p-2 text-left">Label</th>
              <th className="p-2 text-right">Conf</th>
              <th className="p-2 text-left">Routed</th>
              <th className="p-2 text-left">FE</th>
              <th className="p-2 text-left">Reasons</th>
            </tr>
          </thead>
          <tbody>
            {slice.map(({ s, routed }, i) => {
              const t = getTs(s);
              const dt = new Date(t * (t > 2000000000 ? 1 : 1000));
              const p = s.payload || {};
              const routedBadge = routed ? (
                <span
                  className={`px-2 py-0.5 rounded text-xs ${
                    routed.dryrun ? "bg-yellow-100 text-yellow-700" : "bg-green-100 text-green-700"
                  }`}
                >
                  {routed.dryrun ? "dry-run" : "executed"}
                </span>
              ) : (
                <span className="px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-600">no</span>
              );
              const fe = p?.fe;
              const feText = fe ? [
                fe?.symbols?.slice?.(0,2)?.join(", "),
                fe?.tp ? `tp:${fe.tp}` : null,
                fe?.sl ? `sl:${fe.sl}` : null,
                fe?.size ? `sz:${fe.size}` : null
              ].filter(Boolean).join(" • ") : "-";
              return (
                <tr key={i} className="border-t align-top">
                  <td className="p-2 whitespace-nowrap">{dt.toLocaleString()}</td>
                  <td className="p-2">{String(p.text || "").slice(0, 200)}</td>
                  <td className="p-2">{String(p.label || "-")}</td>
                  <td className="p-2 text-right">{Number(p.confidence ?? 0).toFixed(2)}</td>
                  <td className="p-2">{routedBadge}</td>
                  <td className="p-2 text-xs">{feText}</td>
                  <td className="p-2">{Array.isArray(p.reasons) ? p.reasons.join(", ") : "-"}</td>
                </tr>
              );
            })}
            {slice.length === 0 && (
              <tr>
                <td className="p-3 text-gray-500" colSpan={7}>
                  No rows
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="flex items-center gap-3">
        <button
          className="border rounded px-3 py-1"
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          disabled={pageSafe <= 1}
        >
          Prev
        </button>
        <span className="text-sm">
          Page {pageSafe} / {maxPage}
        </span>
        <button
          className="border rounded px-3 py-1"
          onClick={() => setPage((p) => Math.min(maxPage, p + 1))}
          disabled={pageSafe >= maxPage}
        >
          Next
        </button>
      </div>
    </div>
  );
}



