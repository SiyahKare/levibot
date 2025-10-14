import { useEffect, useState } from "react";

interface AIStatusData {
  ok: boolean;
  mode?: string;
  enabled: boolean;
  symbols?: string[];
  max_positions?: number;
  min_confidence?: number;
  cycle_count?: number;
  trades_today?: number;
  risk_params?: {
    stop_loss_pct?: number;
    take_profit_pct?: number;
    min_notional?: number;
    max_notional?: number;
  };
  openai_configured?: boolean;
}

export default function AIStatus() {
  const [status, setStatus] = useState<AIStatusData | null>(null);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState(false);

  const fetchStatus = async () => {
    try {
      const res = await fetch("/automation/status");
      const data = await res.json();
      if (data.ok) {
        setStatus(data);
      }
    } catch (e) {
      console.error("Failed to fetch AI status:", e);
    } finally {
      setLoading(false);
    }
  };

  const toggleBot = async () => {
    if (!status) return;

    setToggling(true);
    try {
      const endpoint = status.enabled
        ? "/automation/stop"
        : "/automation/start";
      const res = await fetch(endpoint, { method: "POST" });
      const data = await res.json();

      if (data.ok) {
        await fetchStatus();
      }
    } catch (e) {
      console.error("Failed to toggle bot:", e);
    } finally {
      setToggling(false);
    }
  };

  const triggerCycle = async () => {
    if (!status?.enabled) return;

    try {
      await fetch("/automation/trigger", { method: "POST" });
      await fetchStatus();
    } catch (e) {
      console.error("Failed to trigger cycle:", e);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 10000); // 10s refresh
    return () => clearInterval(interval);
  }, []);

  if (loading || !status) {
    return (
      <div className="bg-zinc-900 rounded-xl p-6 border border-zinc-800">
        <div className="animate-pulse flex space-x-4">
          <div className="h-12 bg-zinc-800 rounded w-1/3"></div>
          <div className="h-12 bg-zinc-800 rounded w-2/3"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-br from-zinc-900 to-zinc-800 rounded-xl p-6 border border-zinc-700 shadow-2xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div
            className={`w-4 h-4 rounded-full animate-pulse ${
              status.enabled
                ? "bg-green-500 shadow-lg shadow-green-500/50"
                : "bg-gray-500"
            }`}
          ></div>
          <div>
            <h2 className="text-2xl font-bold text-white">
              🤖 AI Trading Engine
            </h2>
            <p className="text-sm text-gray-400">{status.mode}</p>
          </div>
        </div>

        <button
          onClick={toggleBot}
          disabled={toggling}
          className={`px-6 py-3 rounded-lg font-semibold transition-all transform hover:scale-105 ${
            status.enabled
              ? "bg-red-600 hover:bg-red-700 text-white"
              : "bg-green-600 hover:bg-green-700 text-white"
          } ${toggling ? "opacity-50 cursor-not-allowed" : ""}`}
        >
          {toggling ? "⏳" : status.enabled ? "⏸️ STOP" : "▶️ START"}
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-zinc-800/50 rounded-lg p-4 border border-zinc-700">
          <div className="text-gray-400 text-sm mb-1">Cycles</div>
          <div className="text-3xl font-bold text-white">
            {status.cycle_count}
          </div>
        </div>
        <div className="bg-zinc-800/50 rounded-lg p-4 border border-zinc-700">
          <div className="text-gray-400 text-sm mb-1">Trades Today</div>
          <div className="text-3xl font-bold text-blue-400">
            {status.trades_today}
          </div>
        </div>
        <div className="bg-zinc-800/50 rounded-lg p-4 border border-zinc-700">
          <div className="text-gray-400 text-sm mb-1">Max Positions</div>
          <div className="text-3xl font-bold text-purple-400">
            {status.max_positions}
          </div>
        </div>
        <div className="bg-zinc-800/50 rounded-lg p-4 border border-zinc-700">
          <div className="text-gray-400 text-sm mb-1">Min Confidence</div>
          <div className="text-3xl font-bold text-yellow-400">
            {(status.min_confidence * 100).toFixed(0)}%
          </div>
        </div>
      </div>

      {/* Configuration */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {/* Risk Parameters */}
        <div className="bg-zinc-800/50 rounded-lg p-4 border border-zinc-700">
          <h3 className="text-sm font-semibold text-gray-400 mb-3">
            ⚠️ Risk Management
          </h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">Stop Loss:</span>
              <span className="text-red-400 font-semibold">
                {(status.risk_params.stop_loss_pct * 100).toFixed(1)}%
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Take Profit:</span>
              <span className="text-green-400 font-semibold">
                {(status.risk_params.take_profit_pct * 100).toFixed(1)}%
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Position Size:</span>
              <span className="text-white font-mono">
                ${status.risk_params.min_notional} - $
                {status.risk_params.max_notional}
              </span>
            </div>
          </div>
        </div>

        {/* Symbols */}
        <div className="bg-zinc-800/50 rounded-lg p-4 border border-zinc-700">
          <h3 className="text-sm font-semibold text-gray-400 mb-3">
            📊 Tracked Symbols
          </h3>
          <div className="flex flex-wrap gap-2">
            {status.symbols.map((symbol) => (
              <span
                key={symbol}
                className="px-3 py-1 bg-blue-500/20 border border-blue-500/50 rounded-full text-blue-400 text-sm font-mono"
              >
                {symbol.replace("USDT", "")}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Actions */}
      {status.enabled && (
        <div className="flex gap-3">
          <button
            onClick={triggerCycle}
            className="flex-1 px-4 py-2 bg-zinc-700 hover:bg-zinc-600 text-white rounded-lg transition-all font-semibold"
          >
            ⚡ Trigger Cycle Now
          </button>
          <button
            onClick={fetchStatus}
            className="px-4 py-2 bg-zinc-700 hover:bg-zinc-600 text-white rounded-lg transition-all"
          >
            🔄
          </button>
        </div>
      )}

      {!status.enabled && (
        <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
          <p className="text-yellow-400 text-sm">
            ⚠️ AI Trading Bot is currently <strong>disabled</strong>. Click
            START to begin automated trading.
          </p>
        </div>
      )}
    </div>
  );
}
