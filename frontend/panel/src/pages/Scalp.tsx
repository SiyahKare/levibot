/**
 * Scalp Page - LSE Engine Control
 * ─────────────────────────────────────────
 * Low-latency scalping strategy with real-time monitoring
 */

import type { LseHealth, LseRunReq } from "@/lib/api";
import { lseHealth, lsePnlStats, lseRun, lseTradesRecent } from "@/lib/api";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import useSWR from "swr";

export default function ScalpPage() {
  const {
    data: health,
    mutate: refetchHealth,
    isLoading: healthLoading,
  } = useSWR<LseHealth>("/lse/health", lseHealth, { refreshInterval: 5000 });

  const {
    data: pnl,
    mutate: refetchPnl,
    isLoading: pnlLoading,
  } = useSWR("/lse/pnl/stats?hours=24", () => lsePnlStats(24), {
    refreshInterval: 10000,
  });

  const {
    data: trades,
    mutate: refetchTrades,
    isLoading: tradesLoading,
  } = useSWR("/lse/trades/recent", () => lseTradesRecent(50, true), {
    refreshInterval: 10000,
  });

  const [quoteBudget, setQuoteBudget] = useState(150);
  const [isStarting, setIsStarting] = useState(false);
  const [isStopping, setIsStopping] = useState(false);

  const running = !!health?.running;
  const wsConnected = !!health?.ws?.connected;
  const latencyMs = health?.ws?.latency_ms ?? 0;

  // Guards check
  const guardsOk =
    health?.guards?.vol_ok &&
    health?.guards?.spread_ok &&
    health?.guards?.latency_ok &&
    health?.guards?.risk_ok;

  // Start LSE (paper mode)
  const startPaper = async () => {
    if (running) {
      toast.error("Engine is already running");
      return;
    }

    setIsStarting(true);
    try {
      const req: LseRunReq = {
        mode: "paper",
        overrides: {
          quote_budget: quoteBudget,
          cooldown_bars: 5,
        },
      };
      await lseRun(req);
      toast.success(`LSE started (paper mode, $${quoteBudget}/trade)`);
      setTimeout(() => {
        refetchHealth();
        refetchTrades();
      }, 1000);
    } catch (err: any) {
      console.error("LSE start failed:", err);
      toast.error(`Start failed: ${err.message || "Unknown error"}`);
    } finally {
      setIsStarting(false);
    }
  };

  // Stop LSE (soft stop via high cooldown)
  const stopAll = async () => {
    if (!running) {
      toast.error("Engine is not running");
      return;
    }

    setIsStopping(true);
    try {
      // Soft stop: set cooldown to very high value to prevent new trades
      const req: LseRunReq = {
        overrides: { cooldown_bars: 9999 },
      };
      await lseRun(req);
      toast.success("LSE soft-stopped (cooldown → 9999 bars)");
      setTimeout(() => {
        refetchHealth();
      }, 1000);
    } catch (err: any) {
      console.error("LSE stop failed:", err);
      toast.error(`Stop failed: ${err.message || "Unknown error"}`);
    } finally {
      setIsStopping(false);
    }
  };

  // Equity series for sparkline
  const equitySeries: Array<{ t: string; v: number }> = useMemo(() => {
    if (!pnl?.equity_curve || !Array.isArray(pnl.equity_curve)) return [];
    return pnl.equity_curve.map((p: any) => ({
      t: p.ts || p.timestamp || "",
      v: p.equity || 0,
    }));
  }, [pnl]);

  // Sparkline min/max for scaling
  const equityRange = useMemo(() => {
    if (equitySeries.length === 0) return { min: 0, max: 1 };
    const values = equitySeries.map((s) => s.v);
    return { min: Math.min(...values), max: Math.max(...values) };
  }, [equitySeries]);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-100">
          ⚡ LSE — Scalp Engine
        </h1>
        <p className="text-zinc-600 dark:text-zinc-400 mt-2">
          Low-latency scalping strategy for ultra-short timeframes (1m - 5m)
        </p>
      </div>

      {/* Engine Status Card */}
      <div className="grid md:grid-cols-3 gap-4">
        {/* Main Status */}
        <div className="p-4 rounded-2xl shadow bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold">LSE Engine</h2>
            <span
              className={`px-2 py-1 rounded text-xs font-medium ${
                running
                  ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                  : "bg-zinc-200 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400"
              }`}
            >
              {running ? "RUNNING" : "IDLE"}
            </span>
          </div>

          {healthLoading ? (
            <div className="text-sm text-zinc-500">Loading...</div>
          ) : (
            <div className="text-sm space-y-1">
              <div className="flex justify-between">
                <span className="text-zinc-600 dark:text-zinc-400">WS:</span>
                <span
                  className={`font-medium ${
                    wsConnected
                      ? "text-green-600 dark:text-green-400"
                      : "text-red-600 dark:text-red-400"
                  }`}
                >
                  {wsConnected ? "connected" : "disconnected"}
                  {latencyMs > 0 && ` (${Math.round(latencyMs)}ms)`}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-600 dark:text-zinc-400">
                  Guards:
                </span>
                <span
                  className={`font-medium ${
                    guardsOk
                      ? "text-green-600 dark:text-green-400"
                      : "text-yellow-600 dark:text-yellow-400"
                  }`}
                >
                  {guardsOk ? "OK" : "BLOCK"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-600 dark:text-zinc-400">Mode:</span>
                <span className="font-medium">{health?.mode ?? "-"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-600 dark:text-zinc-400">
                  Position:
                </span>
                <span className="font-medium uppercase">
                  {health?.position || "FLAT"}
                </span>
              </div>
            </div>
          )}

          {/* Budget Input */}
          <div className="mt-4 flex items-center gap-2">
            <input
              type="number"
              min={50}
              step={10}
              value={quoteBudget}
              onChange={(e) => setQuoteBudget(Number(e.target.value))}
              disabled={running}
              className="w-28 rounded border border-zinc-300 dark:border-zinc-700 px-2 py-1 bg-white dark:bg-zinc-800 disabled:opacity-50"
            />
            <span className="text-sm opacity-70">USDT / trade</span>
          </div>

          {/* Controls */}
          <div className="mt-4 flex gap-2">
            <button
              onClick={startPaper}
              disabled={running || isStarting || !guardsOk}
              className="flex-1 px-3 py-2 rounded-xl bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium text-sm transition-colors"
            >
              {isStarting ? "⏳" : "▶"} Start (Paper)
            </button>
            <button
              onClick={stopAll}
              disabled={!running || isStopping}
              className="flex-1 px-3 py-2 rounded-xl bg-zinc-200 dark:bg-zinc-800 hover:bg-zinc-300 dark:hover:bg-zinc-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium text-sm transition-colors"
            >
              {isStopping ? "⏳" : "⏸"} Stop
            </button>
            <button
              onClick={() => {
                refetchHealth();
                refetchPnl();
                refetchTrades();
                toast.success("Refreshed");
              }}
              className="px-3 py-2 rounded-xl bg-blue-600 text-white hover:bg-blue-700 font-medium text-sm transition-colors"
            >
              🔄
            </button>
          </div>

          {!guardsOk && (
            <div className="mt-3 p-2 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded text-xs text-yellow-800 dark:text-yellow-400">
              ⚠️ Guards blocking: Check volatility, spread, latency, or risk
              limits
            </div>
          )}
        </div>

        {/* PnL Card */}
        <div className="p-4 rounded-2xl shadow bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800">
          <h3 className="font-semibold mb-2">24h PnL</h3>
          {pnlLoading ? (
            <div className="text-sm text-zinc-500">Loading...</div>
          ) : (
            <>
              <div className="text-2xl font-bold">
                {pnl?.pnl_24h?.toFixed?.(2) ?? "-"}{" "}
                <span className="text-sm font-normal opacity-70">USDT</span>
              </div>
              <div className="text-sm opacity-70 mt-1">
                Trades: {pnl?.trades ?? "-"} | Win rate:{" "}
                {pnl?.win_rate ? `${(pnl.win_rate * 100).toFixed(1)}%` : "-"}
              </div>

              {/* Sparkline */}
              {equitySeries.length > 1 && (
                <div className="mt-3 h-16 w-full overflow-hidden">
                  <svg
                    viewBox={`0 0 ${Math.max(1, equitySeries.length)} 40`}
                    className="w-full h-full"
                    preserveAspectRatio="none"
                  >
                    {equitySeries.map((p, i, arr) => {
                      if (i === 0) return null;
                      const prev = arr[i - 1];
                      const range = equityRange.max - equityRange.min || 1;
                      const y = 40 - ((p.v - equityRange.min) / range) * 38;
                      const yPrev =
                        40 - ((prev.v - equityRange.min) / range) * 38;
                      return (
                        <line
                          key={i}
                          x1={i - 1}
                          y1={yPrev}
                          x2={i}
                          y2={y}
                          strokeWidth="1.5"
                          stroke="currentColor"
                          className="text-blue-500"
                        />
                      );
                    })}
                  </svg>
                </div>
              )}
            </>
          )}
        </div>

        {/* Guards Detail */}
        <div className="p-4 rounded-2xl shadow bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800">
          <h3 className="font-semibold mb-2">Guards</h3>
          {healthLoading ? (
            <div className="text-sm text-zinc-500">Loading...</div>
          ) : (
            <ul className="text-sm space-y-1">
              <li className="flex justify-between">
                <span>Volatility:</span>
                <span
                  className={`font-medium ${
                    health?.guards?.vol_ok
                      ? "text-green-600 dark:text-green-400"
                      : "text-red-600 dark:text-red-400"
                  }`}
                >
                  {health?.guards?.vol_ok ? "OK" : "LOW"}
                </span>
              </li>
              <li className="flex justify-between">
                <span>Spread:</span>
                <span
                  className={`font-medium ${
                    health?.guards?.spread_ok
                      ? "text-green-600 dark:text-green-400"
                      : "text-red-600 dark:text-red-400"
                  }`}
                >
                  {health?.guards?.spread_ok ? "OK" : "WIDE"}
                </span>
              </li>
              <li className="flex justify-between">
                <span>Latency:</span>
                <span
                  className={`font-medium ${
                    health?.guards?.latency_ok
                      ? "text-green-600 dark:text-green-400"
                      : "text-red-600 dark:text-red-400"
                  }`}
                >
                  {health?.guards?.latency_ok ? "OK" : "HIGH"}
                </span>
              </li>
              <li className="flex justify-between">
                <span>Risk:</span>
                <span
                  className={`font-medium ${
                    health?.guards?.risk_ok
                      ? "text-green-600 dark:text-green-400"
                      : "text-red-600 dark:text-red-400"
                  }`}
                >
                  {health?.guards?.risk_ok ? "OK" : "BLOCK"}
                </span>
              </li>
            </ul>
          )}
        </div>
      </div>

      {/* Recent Trades Table */}
      <div className="p-4 rounded-2xl shadow bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold">Recent Trades</h3>
          <button
            onClick={() => {
              refetchTrades();
              toast.success("Trades refreshed");
            }}
            className="px-3 py-1.5 rounded-lg bg-zinc-200 dark:bg-zinc-800 hover:bg-zinc-300 dark:hover:bg-zinc-700 text-sm font-medium transition-colors"
          >
            Refresh
          </button>
        </div>

        {tradesLoading ? (
          <div className="text-sm text-zinc-500 py-6 text-center">
            Loading trades...
          </div>
        ) : (
          <div className="overflow-auto">
            <table className="min-w-full text-sm">
              <thead className="text-left text-zinc-600 dark:text-zinc-400">
                <tr>
                  <th className="py-2 pr-4 font-medium">Time</th>
                  <th className="py-2 pr-4 font-medium">Side</th>
                  <th className="py-2 pr-4 font-medium">Qty</th>
                  <th className="py-2 pr-4 font-medium">Price</th>
                  <th className="py-2 pr-4 font-medium">PnL</th>
                  <th className="py-2 pr-4 font-medium">Reason</th>
                </tr>
              </thead>
              <tbody>
                {(trades?.items ?? []).map((t: any, idx: number) => (
                  <tr
                    key={t.id || idx}
                    className="border-t border-zinc-200/50 dark:border-zinc-800/50"
                  >
                    <td className="py-2 pr-4">
                      {new Date(
                        t.ts || t.time || t.timestamp || Date.now()
                      ).toLocaleTimeString()}
                    </td>
                    <td className="py-2 pr-4">
                      <span
                        className={`font-medium ${
                          t.side === "long" || t.side === "buy"
                            ? "text-green-600 dark:text-green-400"
                            : "text-red-600 dark:text-red-400"
                        }`}
                      >
                        {(t.side || "-").toUpperCase()}
                      </span>
                    </td>
                    <td className="py-2 pr-4">
                      {t.qty?.toFixed?.(6) ?? t.size?.toFixed?.(6) ?? "-"}
                    </td>
                    <td className="py-2 pr-4">
                      {t.price?.toFixed?.(2) ?? "-"}
                    </td>
                    <td
                      className={`py-2 pr-4 font-medium ${
                        (t.pnl ?? 0) > 0
                          ? "text-green-600 dark:text-green-400"
                          : (t.pnl ?? 0) < 0
                          ? "text-red-600 dark:text-red-400"
                          : ""
                      }`}
                    >
                      {t.pnl?.toFixed?.(2) ?? "-"}
                    </td>
                    <td className="py-2 pr-4 text-zinc-600 dark:text-zinc-400">
                      {t.reason ?? "-"}
                    </td>
                  </tr>
                ))}
                {(!trades?.items || trades.items.length === 0) && (
                  <tr>
                    <td
                      colSpan={6}
                      className="py-6 text-center text-zinc-500 dark:text-zinc-400"
                    >
                      No trades yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
