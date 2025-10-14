/**
 * Analytics Page
 * Displays trading analytics with date range selection, confidence deciles, and CSV export
 */
import { DateRange } from "@/components/DateRange";
import { Skeleton } from "@/components/ui/Skeleton";
import { api } from "@/lib/api";
import { useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { toast } from "sonner";
import useSWR from "swr";

export default function Analytics() {
  const [fromIso, setFrom] = useState<string>("");
  const [toIso, setTo] = useState<string>("");
  const [win, setWin] = useState<"24h" | "7d">("24h");

  // Fetch deciles data
  const { data: dec, isLoading: decilesLoading } = useSWR(
    `/analytics/deciles?${win}&${fromIso}&${toIso}`,
    () =>
      api.decilesRange({
        window: win,
        from: fromIso || undefined,
        to: toIso || undefined,
      }),
    { refreshInterval: 30000 }
  );

  // Fetch PnL by strategy
  const { data: pnl, isLoading: pnlLoading } = useSWR(
    `/analytics/pnl?${win}&${fromIso}&${toIso}`,
    () =>
      api.pnlByStrategyRange({
        window: win,
        from: fromIso || undefined,
        to: toIso || undefined,
      }),
    { refreshInterval: 30000 }
  );

  // Fetch recent trades
  const { data: trades } = useSWR(
    "/analytics/trades/recent",
    () => api.tradesRecent(200),
    { refreshInterval: 30000 }
  );

  const decilesData =
    dec?.buckets?.map((b: any) => ({
      decile: b.decile,
      trades: Number(b.count || 0),
      pnl: Number(b.gross_pnl || 0),
      confidence: Number(b.avg_confidence || 0),
    })) || [];

  const pnlData =
    pnl?.items?.map((item: any) => ({
      strategy: item.strategy,
      pnl: Number(item.realized_pnl || 0),
      trades: Number(item.trades || 0),
    })) || [];

  const handleExportCSV = async () => {
    try {
      const res = await api.exportTradesCSV({
        from: fromIso || undefined,
        to: toIso || undefined,
        limit: 5000,
      });
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `trades_${fromIso || "from"}_${toIso || "to"}.csv`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success("CSV exported successfully!");
    } catch (error) {
      toast.error(`Export failed: ${error}`);
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-100">
          Trading Analytics
        </h1>
        <div className="flex flex-wrap items-center gap-2">
          {/* Window Buttons */}
          {(["24h", "7d"] as const).map((w) => (
            <button
              key={w}
              onClick={() => setWin(w)}
              className={`px-3 py-2 rounded-xl text-sm font-medium transition-colors ${
                w === win
                  ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
                  : "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 hover:bg-zinc-200 dark:hover:bg-zinc-700"
              }`}
            >
              {w}
            </button>
          ))}
          {/* Export CSV Button */}
          <button
            onClick={handleExportCSV}
            className="px-3 py-2 rounded-xl bg-emerald-600 text-white hover:bg-emerald-700 transition-colors text-sm font-medium"
          >
            📊 Export CSV
          </button>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Confidence → PnL Chart */}
        <div className="p-6 rounded-2xl shadow bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300">
              Confidence → PnL Deciles
            </h3>
            <span className="text-xs text-zinc-500 dark:text-zinc-400">
              {decilesData.length} buckets
            </span>
          </div>
          <div className="h-80">
            {decilesLoading ? (
              <Skeleton className="h-full" />
            ) : (
              <ResponsiveContainer>
                <BarChart data={decilesData}>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#e4e4e7"
                    className="dark:stroke-zinc-800"
                  />
                  <XAxis
                    dataKey="decile"
                    stroke="#71717a"
                    className="dark:stroke-zinc-400"
                  />
                  <YAxis stroke="#71717a" className="dark:stroke-zinc-400" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#27272a",
                      border: "none",
                      borderRadius: "8px",
                      color: "#fff",
                    }}
                  />
                  <Legend />
                  <Bar dataKey="pnl" fill="#10b981" name="PnL ($)" />
                  <Bar dataKey="trades" fill="#3b82f6" name="Trades" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Date Range Picker */}
        <div className="p-6 rounded-2xl shadow bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800">
          <h3 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300 mb-4">
            📅 Date Range Filter
          </h3>
          <DateRange
            fromIso={fromIso}
            toIso={toIso}
            onChange={(r) => {
              setFrom(r.fromIso || "");
              setTo(r.toIso || "");
            }}
          />
        </div>

        {/* PnL by Strategy */}
        <div className="p-6 rounded-2xl shadow bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300">
              PnL by Strategy
            </h3>
            <span className="text-xs text-zinc-500 dark:text-zinc-400">
              {pnlData.length} strategies
            </span>
          </div>
          <div className="h-80">
            {pnlLoading ? (
              <Skeleton className="h-full" />
            ) : (
              <ResponsiveContainer>
                <BarChart data={pnlData} layout="vertical">
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#e4e4e7"
                    className="dark:stroke-zinc-800"
                  />
                  <XAxis type="number" stroke="#71717a" />
                  <YAxis
                    dataKey="strategy"
                    type="category"
                    stroke="#71717a"
                    width={100}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#27272a",
                      border: "none",
                      borderRadius: "8px",
                      color: "#fff",
                    }}
                  />
                  <Bar dataKey="pnl" fill="#f59e0b" name="PnL ($)" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Recent Trades Table */}
        <div className="p-6 rounded-2xl shadow bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300">
              Recent Trades
            </h3>
            <span className="text-xs text-zinc-500 dark:text-zinc-400">
              {trades?.items?.length || 0} trades
            </span>
          </div>
          <div className="overflow-auto max-h-80">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left border-b border-zinc-200 dark:border-zinc-800">
                  <th className="py-2 text-zinc-600 dark:text-zinc-400">
                    Time
                  </th>
                  <th className="py-2 text-zinc-600 dark:text-zinc-400">
                    Symbol
                  </th>
                  <th className="py-2 text-zinc-600 dark:text-zinc-400">
                    Side
                  </th>
                  <th className="py-2 text-zinc-600 dark:text-zinc-400">
                    Strategy
                  </th>
                  <th className="py-2 text-zinc-600 dark:text-zinc-400">
                    Conf
                  </th>
                </tr>
              </thead>
              <tbody>
                {trades?.items && trades.items.length > 0 ? (
                  trades.items.slice(0, 10).map((t: any, i: number) => (
                    <tr
                      key={i}
                      className="border-b border-zinc-100 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors"
                    >
                      <td className="py-2 font-mono text-xs text-zinc-600 dark:text-zinc-400">
                        {new Date(t.ts).toLocaleTimeString()}
                      </td>
                      <td className="py-2 font-medium text-zinc-900 dark:text-zinc-100">
                        {t.symbol}
                      </td>
                      <td
                        className={`py-2 font-bold uppercase ${
                          t.side === "buy"
                            ? "text-emerald-600 dark:text-emerald-400"
                            : "text-rose-600 dark:text-rose-400"
                        }`}
                      >
                        {t.side}
                      </td>
                      <td className="py-2 text-zinc-700 dark:text-zinc-300">
                        {t.strategy || "—"}
                      </td>
                      <td className="py-2 text-zinc-700 dark:text-zinc-300">
                        {t.confidence
                          ? `${Math.round(t.confidence * 100)}%`
                          : "—"}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td
                      colSpan={5}
                      className="py-4 text-center text-zinc-400 dark:text-zinc-600"
                    >
                      No trades yet
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
