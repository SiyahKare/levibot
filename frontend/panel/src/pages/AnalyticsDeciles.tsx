/**
 * Analytics Page (Deciles)
 * Confidence → PnL deciles analysis with charts
 */
import { api } from "@/lib/api";
import { useState } from "react";
import {
  Bar,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import useSWR from "swr";

export default function AnalyticsDeciles() {
  const [window, setWindow] = useState<"24h" | "7d">("24h");

  const { data, isLoading } = useSWR(
    `/analytics/deciles?${window}`,
    () => api.deciles(window),
    { refreshInterval: 30_000 }
  );

  const { data: trades } = useSWR(
    "/analytics/trades/recent",
    () => api.tradesRecent(100),
    { refreshInterval: 15_000 }
  );

  const buckets =
    data?.buckets?.map((b) => ({
      decile: b.decile,
      trades: b.count,
      avgConf: Number(b.avg_confidence || 0),
      pnl: Number(b.gross_pnl || 0),
    })) || [];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-zinc-900">Analytics</h1>
          <p className="text-zinc-600 mt-2">
            Confidence → PnL correlation analysis
          </p>
        </div>
        <div className="flex gap-2">
          {(["24h", "7d"] as const).map((w) => (
            <button
              key={w}
              onClick={() => setWindow(w)}
              className={`px-4 py-2 rounded-xl font-medium transition-all ${
                w === window
                  ? "bg-zinc-900 text-white"
                  : "bg-zinc-100 text-zinc-700 hover:bg-zinc-200"
              }`}
            >
              {w}
            </button>
          ))}
        </div>
      </div>

      {/* PnL Chart */}
      <div className="p-6 rounded-2xl shadow bg-white border border-zinc-200">
        <h2 className="text-lg font-semibold text-zinc-900 mb-4">
          PnL by Confidence Decile
        </h2>
        {isLoading ? (
          <div className="h-80 flex items-center justify-center text-zinc-500">
            Loading chart...
          </div>
        ) : buckets.length > 0 ? (
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={buckets}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="decile"
                  label={{
                    value: "Confidence Decile",
                    position: "insideBottom",
                    offset: -5,
                  }}
                />
                <YAxis
                  yAxisId="left"
                  label={{
                    value: "Gross PnL (USD)",
                    angle: -90,
                    position: "insideLeft",
                  }}
                />
                <YAxis
                  yAxisId="right"
                  orientation="right"
                  label={{
                    value: "Trades",
                    angle: 90,
                    position: "insideRight",
                  }}
                />
                <Tooltip />
                <Legend />
                <Bar yAxisId="left" dataKey="pnl" name="PnL" fill="#10b981">
                  {buckets.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.pnl >= 0 ? "#10b981" : "#ef4444"}
                    />
                  ))}
                </Bar>
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="trades"
                  name="Trades"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={{ fill: "#3b82f6" }}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="h-80 flex items-center justify-center text-zinc-500">
            No data available
          </div>
        )}
        {data?.note && (
          <div className="mt-4 p-3 rounded-lg bg-amber-50 border border-amber-200">
            <p className="text-sm text-amber-800">ℹ️ {data.note}</p>
          </div>
        )}
      </div>

      {/* Deciles Table */}
      <div className="p-6 rounded-2xl shadow bg-white border border-zinc-200 overflow-x-auto">
        <h2 className="text-lg font-semibold text-zinc-900 mb-4">
          Decile Breakdown
        </h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-200">
              <th className="text-left py-2 px-3 font-semibold text-zinc-700">
                Decile
              </th>
              <th className="text-right py-2 px-3 font-semibold text-zinc-700">
                Trades
              </th>
              <th className="text-right py-2 px-3 font-semibold text-zinc-700">
                Avg Confidence
              </th>
              <th className="text-right py-2 px-3 font-semibold text-zinc-700">
                Gross PnL
              </th>
            </tr>
          </thead>
          <tbody>
            {buckets.map((bucket) => (
              <tr
                key={bucket.decile}
                className="border-b border-zinc-100 hover:bg-zinc-50"
              >
                <td className="py-2 px-3 font-medium">{bucket.decile}</td>
                <td className="py-2 px-3 text-right">{bucket.trades}</td>
                <td className="py-2 px-3 text-right">
                  {(bucket.avgConf * 100).toFixed(1)}%
                </td>
                <td
                  className={`py-2 px-3 text-right font-semibold ${
                    bucket.pnl >= 0 ? "text-emerald-600" : "text-rose-600"
                  }`}
                >
                  {bucket.pnl >= 0 ? "+" : ""}${bucket.pnl.toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Recent Trades with Reasons */}
      <div className="p-6 rounded-2xl shadow bg-white border border-zinc-200 overflow-x-auto">
        <h2 className="text-lg font-semibold text-zinc-900 mb-4">
          Recent Trades (with Reason)
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-200">
                <th className="text-left py-2 px-3 font-semibold text-zinc-700">
                  Time
                </th>
                <th className="text-left py-2 px-3 font-semibold text-zinc-700">
                  Symbol
                </th>
                <th className="text-center py-2 px-3 font-semibold text-zinc-700">
                  Side
                </th>
                <th className="text-right py-2 px-3 font-semibold text-zinc-700">
                  Qty
                </th>
                <th className="text-right py-2 px-3 font-semibold text-zinc-700">
                  Price
                </th>
                <th className="text-center py-2 px-3 font-semibold text-zinc-700">
                  Strategy
                </th>
                <th className="text-left py-2 px-3 font-semibold text-zinc-700">
                  Reason
                </th>
              </tr>
            </thead>
            <tbody>
              {trades?.items?.map((t: any, i: number) => (
                <tr
                  key={i}
                  className="border-b border-zinc-100 hover:bg-zinc-50"
                >
                  <td className="py-2 px-3 text-xs text-zinc-600">
                    {t.ts
                      ? new Date(t.ts).toLocaleString("en-US", {
                          month: "short",
                          day: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        })
                      : "-"}
                  </td>
                  <td className="py-2 px-3 font-medium">{t.symbol || "-"}</td>
                  <td
                    className={`py-2 px-3 text-center font-semibold ${
                      t.side === "buy" ? "text-emerald-600" : "text-rose-600"
                    }`}
                  >
                    {t.side?.toUpperCase() || "-"}
                  </td>
                  <td className="py-2 px-3 text-right">{t.qty || "-"}</td>
                  <td className="py-2 px-3 text-right">
                    ${Number(t.price || 0).toLocaleString()}
                  </td>
                  <td className="py-2 px-3 text-center">
                    <span className="px-2 py-1 rounded text-xs bg-zinc-100 text-zinc-700">
                      {t.strategy || "unknown"}
                    </span>
                  </td>
                  <td
                    className="py-2 px-3 max-w-xs truncate text-zinc-600"
                    title={t.reason || ""}
                  >
                    {t.reason || "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {(!trades?.items || trades.items.length === 0) && (
          <div className="text-center py-8 text-zinc-500">
            No trades available
          </div>
        )}
      </div>
    </div>
  );
}
