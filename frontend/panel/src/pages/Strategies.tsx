/**
 * Strategies Page
 * Enable/disable trading strategies with toggle switches
 */
import { api } from "@/lib/api";
import { useState } from "react";
import { toast } from "sonner";
import useSWR, { mutate } from "swr";

export default function Strategies() {
  const { data, isLoading } = useSWR("/strategy/", api.strategies, {
    refreshInterval: 10_000,
  });

  const { data: pnl } = useSWR(
    "/analytics/pnl/by_strategy?24h",
    () => api.pnlByStrategy("24h"),
    { refreshInterval: 15_000 }
  );

  const [busy, setBusy] = useState<string | null>(null);

  const handleToggle = async (name: string, enabled: boolean) => {
    const key = "/strategy/";
    setBusy(name);

    // Optimistic update
    mutate(
      key,
      (prev: any) =>
        prev?.map((s: any) => (s.name === name ? { ...s, enabled } : s)),
      false
    );

    try {
      await api.toggleStrategy(name, enabled);
      toast.success(`${name}: ${enabled ? "enabled" : "disabled"}`);
    } catch (error: any) {
      console.error("Toggle failed:", error);
      toast.error(`Failed: ${error.message || "Unknown error"}`);
    } finally {
      mutate(key);
      setBusy(null);
    }
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="text-zinc-500">Loading strategies...</div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-zinc-900">Trading Strategies</h1>
        <p className="text-zinc-600 mt-2">
          Enable or disable individual trading strategies
        </p>
      </div>

      <div className="grid gap-4">
        {data?.map((strategy) => (
          <div
            key={strategy.name}
            className="flex items-center justify-between p-6 rounded-2xl shadow bg-white border border-zinc-200 hover:border-zinc-300 transition-colors"
          >
            <div className="flex-1">
              <div className="flex items-center gap-3">
                <h3 className="text-lg font-semibold text-zinc-900">
                  {strategy.name}
                </h3>
                <span
                  className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                    strategy.enabled
                      ? "bg-emerald-100 text-emerald-700"
                      : "bg-zinc-100 text-zinc-600"
                  }`}
                >
                  {strategy.enabled ? "Enabled" : "Disabled"}
                </span>
              </div>
              <p className="text-sm text-zinc-600 mt-1">
                {strategy.description}
              </p>
              {pnl?.items?.find((x) => x.strategy === strategy.name) && (
                <div className="mt-2">
                  <span
                    className={`px-2 py-1 rounded text-xs font-medium ${
                      (pnl.items.find((x) => x.strategy === strategy.name)
                        ?.realized_pnl || 0) >= 0
                        ? "bg-emerald-100 text-emerald-700"
                        : "bg-rose-100 text-rose-700"
                    }`}
                  >
                    PnL:{" "}
                    {(
                      pnl.items.find((x) => x.strategy === strategy.name)
                        ?.realized_pnl || 0
                    ).toFixed(2)}{" "}
                    /{" "}
                    {pnl.items.find((x) => x.strategy === strategy.name)
                      ?.trades || 0}{" "}
                    trades
                  </span>
                </div>
              )}
            </div>

            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                className="sr-only peer"
                checked={strategy.enabled}
                disabled={busy === strategy.name}
                onChange={(e) => handleToggle(strategy.name, e.target.checked)}
              />
              <div className="w-14 h-7 bg-zinc-300 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-emerald-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[4px] after:bg-white after:border-zinc-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-emerald-600"></div>
            </label>
          </div>
        ))}
      </div>

      {!data || data.length === 0 ? (
        <div className="p-6 rounded-2xl bg-zinc-50 border border-zinc-200 text-center">
          <p className="text-zinc-600">No strategies available</p>
        </div>
      ) : null}
    </div>
  );
}
