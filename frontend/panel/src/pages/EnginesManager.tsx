/**
 * Engines Manager Page
 * Multi-engine control panel with real-time status via SSE
 * Sprint-10 Epic-1 Integration
 */
import { api, API_BASE } from "@/lib/api";
import { openSSE } from "@/lib/sse";
import { useEffect, useState } from "react";
import { toast } from "sonner";

type EngineStatus = "running" | "stopped" | "degraded" | "error";

type EngineRow = {
  symbol: string;
  status: EngineStatus;
  inference_p95_ms?: number;
  uptime_s?: number;
  trades_today?: number;
  last_error?: string;
};

export default function EnginesManager() {
  const [engines, setEngines] = useState<EngineRow[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Initial load
    api.engines
      .list()
      .then((list) => {
        setEngines(list);
        setLoading(false);
      })
      .catch((error) => {
        toast.error(`Failed to load engines: ${error.message}`);
        setLoading(false);
      });

    // SSE real-time updates
    const closeSSE = openSSE(`${API_BASE}/stream/engines`, {
      onMessage: (msg) => {
        // Expected payload: {symbol, status, inference_p95_ms, uptime_s, trades_today}
        setEngines((prev) => {
          const idx = prev.findIndex((e) => e.symbol === msg.symbol);
          const updated: EngineRow = {
            symbol: msg.symbol,
            status: msg.status || "stopped",
            inference_p95_ms: msg.inference_p95_ms,
            uptime_s: msg.uptime_s,
            trades_today: msg.trades_today,
            last_error: msg.last_error,
          };

          if (idx >= 0) {
            // Update existing
            const next = [...prev];
            next[idx] = { ...next[idx], ...updated };
            return next;
          } else {
            // Add new
            return [...prev, updated];
          }
        });
      },
      onError: (error) => {
        console.warn("[EnginesManager] SSE error:", error);
      },
    });

    return closeSSE;
  }, []);

  const handleAction = async (action: "start" | "stop", symbol: string) => {
    setBusy(symbol);
    try {
      if (action === "start") {
        await api.engines.start(symbol);
        toast.success(`Engine started: ${symbol}`);
      } else {
        await api.engines.stop(symbol);
        toast.info(`Engine stopped: ${symbol}`);
      }

      // Refresh status
      const health = await api.engines.health(symbol);
      setEngines((prev) =>
        prev.map((e) =>
          e.symbol === symbol ? { ...e, status: health.status } : e
        )
      );
    } catch (error: any) {
      toast.error(`Action failed: ${error.message}`);
    } finally {
      setBusy(null);
    }
  };

  const statusColor = (status: EngineStatus) => {
    switch (status) {
      case "running":
        return "text-emerald-600 dark:text-emerald-400";
      case "degraded":
        return "text-amber-600 dark:text-amber-400";
      case "error":
        return "text-rose-600 dark:text-rose-400";
      default:
        return "text-zinc-500 dark:text-zinc-400";
    }
  };

  const statusBadge = (status: EngineStatus) => {
    switch (status) {
      case "running":
        return "bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300";
      case "degraded":
        return "bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300";
      case "error":
        return "bg-rose-100 dark:bg-rose-900/30 text-rose-700 dark:text-rose-300";
      default:
        return "bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400";
    }
  };

  if (loading) {
    return (
      <main className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-zinc-200 dark:bg-zinc-800 rounded w-48"></div>
          <div className="h-64 bg-zinc-200 dark:bg-zinc-800 rounded"></div>
        </div>
      </main>
    );
  }

  return (
    <main className="p-6 space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
          Engine Manager
        </h1>
        <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-1">
          Multi-symbol trading engines with real-time monitoring
        </p>
      </header>

      {engines.length === 0 ? (
        <div className="p-12 text-center border border-dashed border-zinc-300 dark:border-zinc-700 rounded-2xl">
          <div className="text-4xl mb-4">🤖</div>
          <h3 className="text-lg font-medium text-zinc-900 dark:text-zinc-100 mb-2">
            No engines configured
          </h3>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            Add symbols to <code className="px-2 py-1 bg-zinc-100 dark:bg-zinc-800 rounded">backend/src/app/main.py</code> to start trading
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm border border-zinc-200 dark:border-zinc-800 rounded-lg">
            <thead className="bg-zinc-50 dark:bg-zinc-900">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-zinc-700 dark:text-zinc-300">
                  Symbol
                </th>
                <th className="px-4 py-3 text-left font-medium text-zinc-700 dark:text-zinc-300">
                  Status
                </th>
                <th className="px-4 py-3 text-right font-medium text-zinc-700 dark:text-zinc-300">
                  Inference (p95)
                </th>
                <th className="px-4 py-3 text-right font-medium text-zinc-700 dark:text-zinc-300">
                  Uptime
                </th>
                <th className="px-4 py-3 text-right font-medium text-zinc-700 dark:text-zinc-300">
                  Trades Today
                </th>
                <th className="px-4 py-3 text-right font-medium text-zinc-700 dark:text-zinc-300">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
              {engines.map((engine) => (
                <tr
                  key={engine.symbol}
                  className="hover:bg-zinc-50 dark:hover:bg-zinc-900/50 transition-colors"
                >
                  <td className="px-4 py-3 font-medium text-zinc-900 dark:text-zinc-100">
                    {engine.symbol}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusBadge(
                        engine.status
                      )}`}
                    >
                      <span
                        className={`w-2 h-2 rounded-full mr-1.5 ${
                          engine.status === "running"
                            ? "bg-emerald-500 animate-pulse"
                            : engine.status === "degraded"
                            ? "bg-amber-500"
                            : "bg-zinc-400"
                        }`}
                      ></span>
                      {engine.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-sm text-zinc-700 dark:text-zinc-300">
                    {engine.inference_p95_ms !== undefined
                      ? `${engine.inference_p95_ms.toFixed(1)}ms`
                      : "-"}
                  </td>
                  <td className="px-4 py-3 text-right text-zinc-700 dark:text-zinc-300">
                    {engine.uptime_s !== undefined
                      ? formatUptime(engine.uptime_s)
                      : "-"}
                  </td>
                  <td className="px-4 py-3 text-right text-zinc-700 dark:text-zinc-300">
                    {engine.trades_today ?? "-"}
                  </td>
                  <td className="px-4 py-3 text-right space-x-2">
                    <button
                      disabled={
                        busy === engine.symbol || engine.status === "running"
                      }
                      onClick={() => handleAction("start", engine.symbol)}
                      className="px-3 py-1.5 rounded-lg text-xs font-medium bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      Start
                    </button>
                    <button
                      disabled={
                        busy === engine.symbol || engine.status !== "running"
                      }
                      onClick={() => handleAction("stop", engine.symbol)}
                      className="px-3 py-1.5 rounded-lg text-xs font-medium bg-rose-600 text-white hover:bg-rose-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      Stop
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Legend */}
      <footer className="flex items-center gap-6 text-xs text-zinc-500 dark:text-zinc-400">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
          <span>Running</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-amber-500"></span>
          <span>Degraded</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-rose-500"></span>
          <span>Error</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-zinc-400"></span>
          <span>Stopped</span>
        </div>
      </footer>
    </main>
  );
}

function formatUptime(seconds: number): string {
  if (seconds < 60) return `${seconds.toFixed(0)}s`;
  if (seconds < 3600) return `${(seconds / 60).toFixed(0)}m`;
  return `${(seconds / 3600).toFixed(1)}h`;
}

