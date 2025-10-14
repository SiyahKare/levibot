import { http } from "@/lib/api";
import { useMemo } from "react";
import useSWR from "swr";

export default function WatchlistPage() {
  // Fetch universe
  const { data: universe, isLoading: universeLoading } = useSWR<any>(
    "/universe/active",
    () => http("/universe/active"),
    { refreshInterval: 15000 }
  );

  // Fetch feed health
  const { data: feedHealth } = useSWR<any>(
    "/feed/health",
    () => http("/feed/health"),
    { refreshInterval: 10000 }
  );

  const allSymbols = useMemo(() => {
    if (!universe?.ok) return [];
    return universe.symbols || [];
  }, [universe]);

  const coreSymbols = useMemo(() => {
    if (!universe?.ok) return [];
    return universe.core || [];
  }, [universe]);

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-100">
          Watchlist
        </h1>
        <div className="flex items-center gap-4">
          <div className="text-sm text-zinc-600 dark:text-zinc-400">
            {allSymbols.length} symbols active
          </div>
          <div
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg ${
              feedHealth?.ws_connected
                ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                : "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
            }`}
          >
            <div
              className={`w-2 h-2 rounded-full ${
                feedHealth?.ws_connected
                  ? "bg-green-600 animate-pulse"
                  : "bg-red-600"
              }`}
            />
            <span className="text-xs font-medium">
              {feedHealth?.ws_connected ? "LIVE" : "DISCONNECTED"}
            </span>
          </div>
        </div>
      </div>

      {/* Core Symbols Grid */}
      <div>
        <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100 mb-3">
          Core Symbols (High Liquidity)
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {coreSymbols.map((symbol: string) => (
            <SymbolCard key={symbol} symbol={symbol} isCore={true} />
          ))}
        </div>
      </div>

      {/* Tier 2 Symbols Grid */}
      <div>
        <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100 mb-3">
          Tier 2 Symbols (Rotation)
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {allSymbols
            .filter((s: string) => !coreSymbols.includes(s))
            .map((symbol: string) => (
              <SymbolCard key={symbol} symbol={symbol} isCore={false} />
            ))}
        </div>
      </div>

      {/* Loading State */}
      {universeLoading && (
        <div className="text-center py-12">
          <div className="animate-spin text-4xl">⏳</div>
          <p className="mt-4 text-zinc-600 dark:text-zinc-400">
            Loading universe...
          </p>
        </div>
      )}
    </div>
  );
}

function SymbolCard({ symbol, isCore }: { symbol: string; isCore: boolean }) {
  // Fetch health for this symbol (stub for now)
  const { data: health } = useSWR<any>(
    `/lse/health/${symbol}`,
    () => http(`/lse/health/${symbol}`),
    { refreshInterval: 10000, revalidateOnFocus: false }
  );

  const running = health?.running || false;
  const price = health?.features?.price || 0;
  const vol1h = health?.features?.vol_1h || 0;
  const spread = health?.features?.spread_bps || 0;

  return (
    <div
      className={`p-4 rounded-2xl shadow cursor-pointer transition-all hover:scale-105 ${
        isCore
          ? "bg-gradient-to-br from-blue-50 to-white dark:from-blue-900/20 dark:to-zinc-900 border border-blue-200 dark:border-blue-800"
          : "bg-white dark:bg-zinc-900"
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-bold text-zinc-900 dark:text-zinc-100">
          {symbol.replace("USDT", "")}
        </h3>
        {running && (
          <span className="px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
            RUNNING
          </span>
        )}
      </div>

      <div className="space-y-1 text-sm text-zinc-700 dark:text-zinc-300">
        <div className="flex justify-between">
          <span className="text-zinc-600 dark:text-zinc-400">Price:</span>
          <span className="font-medium">
            {price > 0 ? `$${price.toFixed(2)}` : "-"}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-zinc-600 dark:text-zinc-400">Vol (1h):</span>
          <span className="font-medium">
            {vol1h > 0 ? `${(vol1h * 100).toFixed(2)}%` : "-"}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-zinc-600 dark:text-zinc-400">Spread:</span>
          <span className="font-medium">
            {spread > 0 ? `${spread.toFixed(1)} bps` : "-"}
          </span>
        </div>
      </div>

      <button
        onClick={() => {
          window.location.href = `/scalp?symbol=${symbol}`;
        }}
        className="mt-3 w-full px-3 py-1.5 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700"
      >
        Trade
      </button>
    </div>
  );
}
