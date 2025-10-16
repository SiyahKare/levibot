/**
 * Fibonacci Retracement Levels Card
 * Displays Fibonacci levels and current price position
 */
import { api } from "@/lib/api";
import { useState } from "react";
import useSWR from "swr";

interface FibonacciCardProps {
  symbol: string;
  timeframe?: string;
  window?: number;
}

export function FibonacciCard({
  symbol,
  timeframe = "1m",
  window = 2880,
}: FibonacciCardProps) {
  const [showLevels, setShowLevels] = useState(true);

  const { data: fib, error } = useSWR(
    `/ta/fibonacci?symbol=${symbol}&timeframe=${timeframe}&window=${window}`,
    () => api.ta.fibonacci(symbol, timeframe, window),
    { refreshInterval: 30_000 } // Refresh every 30s
  );

  if (error) {
    return (
      <div className="p-6 rounded-2xl shadow bg-white border border-zinc-200">
        <div className="text-sm text-red-500">Failed to load Fibonacci levels</div>
      </div>
    );
  }

  if (!fib) {
    return (
      <div className="p-6 rounded-2xl shadow bg-white border border-zinc-200">
        <div className="text-sm text-zinc-500">Loading Fibonacci levels…</div>
      </div>
    );
  }

  // Determine current zone
  const getZoneBadge = () => {
    const { last_close, levels } = fib;
    if (last_close < levels["0.618"]) {
      return (
        <span className="text-xs px-2 py-1 rounded bg-emerald-100 text-emerald-700 font-medium">
          🟢 Oversold Zone
        </span>
      );
    } else if (last_close > levels["0.382"]) {
      return (
        <span className="text-xs px-2 py-1 rounded bg-rose-100 text-rose-700 font-medium">
          🔴 Overbought Zone
        </span>
      );
    } else {
      return (
        <span className="text-xs px-2 py-1 rounded bg-blue-100 text-blue-700 font-medium">
          🔵 Mean Reversion Zone
        </span>
      );
    }
  };

  return (
    <div className="p-6 rounded-2xl shadow bg-white border border-zinc-200">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="text-sm text-zinc-500 font-medium mb-1">
            Fibonacci Retracement
          </div>
          <div className="text-lg font-semibold text-zinc-900">
            {fib.symbol}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {getZoneBadge()}
          <button
            onClick={() => setShowLevels(!showLevels)}
            className="text-xs px-3 py-1.5 rounded border border-zinc-300 hover:bg-zinc-50 transition-colors"
          >
            {showLevels ? "Hide" : "Show"} Levels
          </button>
        </div>
      </div>

      {/* Swing High/Low */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="p-3 bg-zinc-50 rounded-lg">
          <div className="text-xs text-zinc-500 mb-1">Swing High</div>
          <div className="text-sm font-semibold text-zinc-900">
            ${fib.swing_high.toLocaleString()}
          </div>
        </div>
        <div className="p-3 bg-blue-50 rounded-lg">
          <div className="text-xs text-blue-600 mb-1">Current Price</div>
          <div className="text-sm font-semibold text-blue-900">
            ${fib.last_close.toLocaleString()}
          </div>
        </div>
        <div className="p-3 bg-zinc-50 rounded-lg">
          <div className="text-xs text-zinc-500 mb-1">Swing Low</div>
          <div className="text-sm font-semibold text-zinc-900">
            ${fib.swing_low.toLocaleString()}
          </div>
        </div>
      </div>

      {/* Fibonacci Levels */}
      {showLevels && (
        <div className="space-y-2">
          <div className="text-xs text-zinc-500 font-medium mb-2">
            Retracement Levels
          </div>
          {Object.entries(fib.levels)
            .sort(([, a], [, b]) => b - a)
            .map(([level, price]) => {
              const dist = fib.dist[level as keyof typeof fib.dist];
              const isNear = Math.abs(dist) < 0.5; // Within 0.5%
              const isGolden = level === "0.618";

              return (
                <div
                  key={level}
                  className={`flex items-center justify-between p-2 rounded ${
                    isNear ? "bg-yellow-50" : "bg-zinc-50"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs font-mono ${
                        isGolden ? "text-yellow-600 font-semibold" : "text-zinc-600"
                      }`}
                    >
                      {level}
                      {isGolden && " 🌟"}
                    </span>
                    <span className="text-sm text-zinc-900">
                      ${price.toLocaleString(undefined, {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </span>
                  </div>
                  <span
                    className={`text-xs font-medium ${
                      dist > 0
                        ? "text-rose-600"
                        : dist < 0
                        ? "text-emerald-600"
                        : "text-zinc-500"
                    }`}
                  >
                    {dist > 0 ? "+" : ""}
                    {dist.toFixed(2)}%
                  </span>
                </div>
              );
            })}
        </div>
      )}

      {/* Footer Info */}
      <div className="mt-4 pt-3 border-t border-zinc-200 text-xs text-zinc-500">
        Window: {window} bars ({timeframe}) • Updated:{" "}
        {new Date(fib.ts).toLocaleTimeString()}
      </div>
    </div>
  );
}

