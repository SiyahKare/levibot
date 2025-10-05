import { useEffect, useMemo, useState } from "react";
import { fetchClosed } from "../api";
import type { EventRec } from "../types";
import { getTs } from "../types";

type Side = "all" | "buy" | "sell";

export default function Trades() {
  const [raw, setRaw] = useState<EventRec[]>([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  // Filters
  const [symbol, setSymbol] = useState<string>("");
  const [side, setSide] = useState<Side>("all");

  // Pagination
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);

  useEffect(() => {
    let alive = true;

    const pull = async () => {
      try {
        setLoading(true);
        const data = await fetchClosed(300);
        if (!alive) return;
        setRaw(Array.isArray(data) ? data : []);
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

  const filtered = useMemo(() => {
    const sym = symbol.trim().toUpperCase();
    return raw.filter((r) => {
      const s = (r.symbol || r.payload?.symbol || "").toUpperCase();
      const payloadSide = (r.payload?.side || "").toLowerCase();
      const symOk = sym === "" || s.includes(sym);
      const sideOk = side === "all" || payloadSide === side;
      return symOk && sideOk;
    });
  }, [raw, symbol, side]);

  const sorted = useMemo(() => [...filtered].sort((a, b) => getTs(b) - getTs(a)), [filtered]);

  const total = sorted.length;
  const maxPage = Math.max(1, Math.ceil(total / pageSize));
  const pageSafe = Math.min(page, maxPage);
  const slice = useMemo(() => {
    const start = (pageSafe - 1) * pageSize;
    return sorted.slice(start, start + pageSize);
  }, [sorted, pageSafe, pageSize]);

  const uniqueSymbols = useMemo(() => {
    const set = new Set<string>();
    raw.forEach((r) => {
      const s = (r.symbol || r.payload?.symbol || "").toUpperCase();
      if (s) set.add(s);
    });
    return Array.from(set).sort();
  }, [raw]);

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-xl font-semibold">Trades (POSITION_CLOSED)</h1>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-end">
        <div className="flex flex-col">
          <label className="text-sm text-gray-500">Symbol</label>
          <input
            value={symbol}
            onChange={(e) => {
              setSymbol(e.target.value);
              setPage(1);
            }}
            list="symbols"
            placeholder="e.g. ETHUSDT / ETH/USDT"
            className="border rounded px-2 py-1"
          />
          <datalist id="symbols">
            {uniqueSymbols.map((s) => (
              <option key={s} value={s} />
            ))}
          </datalist>
        </div>

        <div className="flex flex-col">
          <label className="text-sm text-gray-500">Side</label>
          <select
            value={side}
            onChange={(e) => {
              setSide(e.target.value as Side);
              setPage(1);
            }}
            className="border rounded px-2 py-1"
          >
            <option value="all">all</option>
            <option value="buy">buy</option>
            <option value="sell">sell</option>
          </select>
        </div>

        <div className="flex flex-col">
          <label className="text-sm text-gray-500">Page size</label>
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(parseInt(e.target.value));
              setPage(1);
            }}
            className="border rounded px-2 py-1"
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

      {/* Table */}
      <div className="overflow-auto border rounded">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left p-2 w-[160px]">Time</th>
              <th className="text-left p-2">Symbol</th>
              <th className="text-left p-2">Side</th>
              <th className="text-right p-2">Qty</th>
              <th className="text-right p-2">Price</th>
              <th className="text-right p-2">PnL (USDT)</th>
              <th className="text-left p-2">Trace</th>
            </tr>
          </thead>
          <tbody>
            {slice.map((r, i) => {
              const ts = getTs(r);
              const dt = new Date(ts * (ts > 2000000000 ? 1 : 1000)); // support sec or ms
              const payload = r.payload || {};
              const sym = (r.symbol || payload.symbol || "") as string;
              const s = (payload.side || "") as string;
              const qty = Number(payload.qty ?? 0);
              const price = Number(payload.price ?? 0);
              const pnl = Number(payload.pnl_usdt ?? payload.pnl ?? 0);
              const trace = r.trace_id || "";
              return (
                <tr key={i} className="border-t">
                  <td className="p-2 whitespace-nowrap">{dt.toLocaleString()}</td>
                  <td className="p-2">{sym}</td>
                  <td className="p-2 capitalize">{s || "-"}</td>
                  <td className="p-2 text-right">{qty ? qty.toFixed(6) : "-"}</td>
                  <td className="p-2 text-right">{price ? price.toFixed(4) : "-"}</td>
                  <td className="p-2 text-right">{pnl ? pnl.toFixed(2) : "0.00"}</td>
                  <td className="p-2">{trace?.slice(0, 12) || "-"}</td>
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

      {/* Pagination */}
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
