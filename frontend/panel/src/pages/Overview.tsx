/**
 * Overview Page
 * Main dashboard with equity, PnL, AI signals, and live status
 */
import { ReplayBadge } from "@/components/ReplayBadge";
import { SSEStatus } from "@/components/SSEStatus";
import { api } from "@/lib/api";
import { toast } from "sonner";
import useSWR from "swr";

/**
 * Model Selector Component
 * Displays available models and allows switching between them
 */
function ModelSelector() {
  const { data, mutate } = useSWR("/ai/models", api.aiModels, {
    refreshInterval: 15_000,
  });

  if (!data) {
    return (
      <div className="p-6 rounded-2xl shadow bg-white border border-zinc-200">
        <div className="text-sm text-zinc-500">Loading models…</div>
      </div>
    );
  }

  return (
    <div className="p-6 rounded-2xl shadow bg-white border border-zinc-200">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-sm text-zinc-500 font-medium mb-1">
            Selected Model
          </div>
          <div className="text-xl font-semibold text-zinc-900">
            {data.current}
          </div>
        </div>
        <div className="flex gap-2">
          {data.models.map((m) => (
            <button
              key={m}
              onClick={async () => {
                try {
                  await api.aiSelect(m);
                  toast.success(`Model switched to ${m}`);
                  mutate(); // Refresh model list
                } catch (error) {
                  toast.error(`Failed to switch model: ${error}`);
                }
              }}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
                m === data.current
                  ? "bg-zinc-900 text-white"
                  : "bg-zinc-100 text-zinc-700 hover:bg-zinc-200"
              }`}
            >
              {m}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

/**
 * Recent Predictions Component
 * Shows latest ML model predictions with timestamps
 */
function RecentPreds() {
  const { data } = useSWR(
    "/analytics/predictions/recent",
    () => api.predsRecent(20),
    { refreshInterval: 10_000 }
  );

  return (
    <div className="p-6 rounded-2xl shadow bg-white border border-zinc-200">
      <div className="text-sm font-semibold text-zinc-700 mb-3">
        🤖 Recent Predictions
      </div>
      <div className="space-y-1 text-sm max-h-64 overflow-auto">
        {data?.items && data.items.length > 0 ? (
          data.items.map((p: any, i: number) => (
            <div key={i} className="flex justify-between items-center py-1.5">
              <span className="font-mono text-xs text-zinc-500">
                {new Date(p.ts * 1000).toLocaleTimeString()}
              </span>
              <span className="font-medium text-zinc-900">{p.symbol}</span>
              <span className="text-xs px-2 py-1 rounded bg-blue-100 text-blue-700">
                {p.model}
              </span>
              <span className="font-semibold text-emerald-600">
                {Math.round((p.prob_up || 0) * 100)}%
              </span>
            </div>
          ))
        ) : (
          <div className="text-zinc-400 py-4 text-center">
            No predictions yet
          </div>
        )}
      </div>
    </div>
  );
}

export default function Overview() {
  const { data: summary } = useSWR("/paper/summary", api.paperSummary, {
    refreshInterval: 10_000,
  });

  const { data: ai } = useSWR(
    "/ai/predict?BTCUSDT",
    () => api.aiPredict("BTCUSDT", "60s"),
    { refreshInterval: 10_000 }
  );

  const { data: signals } = useSWR("/ops/signal_log", () => api.signalLog(20), {
    refreshInterval: 10_000,
  });

  const { data: enginesList } = useSWR("/engines", api.engines.list, {
    refreshInterval: 5_000,
  });

  // Filter running engines
  const runningEngines =
    enginesList?.filter((e: any) => e.status === "running") || [];

  const stats = summary?.stats || {};
  const equity = stats.total_equity ?? 0;
  const pnl = stats.total_pnl ?? 0;
  const pnlPct = stats.total_pnl_pct ?? 0;
  const trades = stats.total_trades ?? 0;
  const winRate = stats.win_rate ?? 0;
  const openPos = stats.open_positions ?? 0;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-zinc-900">LEVIBOT Overview</h1>
        <div className="flex items-center gap-3">
          <SSEStatus />
          <ReplayBadge />
        </div>
      </div>

      {/* Main Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Paper Trading Start */}
        <div className="p-6 rounded-2xl shadow bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200">
          <div className="text-sm text-blue-700 font-medium mb-1">
            💰 Paper Start
          </div>
          <div className="text-3xl font-bold text-blue-900">$1,000.00</div>
          <div className="text-xs text-blue-600 mt-1">Simulated Capital</div>
        </div>

        {/* Equity */}
        <div className="p-6 rounded-2xl shadow bg-white border border-zinc-200">
          <div className="text-sm text-zinc-500 font-medium mb-1">
            Current Equity
          </div>
          <div className="text-3xl font-bold text-zinc-900">
            $
            {equity.toLocaleString("en-US", {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </div>
          <div className="text-xs text-zinc-500 mt-1">
            🔴 LIVE Paper Trading
          </div>
        </div>

        {/* PnL */}
        <div className="p-6 rounded-2xl shadow bg-white border border-zinc-200">
          <div className="text-sm text-zinc-500 font-medium mb-1">
            Total PnL
          </div>
          <div
            className={`text-3xl font-bold ${
              pnl >= 0 ? "text-emerald-600" : "text-rose-600"
            }`}
          >
            {pnl >= 0 ? "+" : ""}${pnl.toFixed(2)}
            <span className="text-lg ml-2">
              ({pnlPct >= 0 ? "+" : ""}
              {pnlPct.toFixed(2)}%)
            </span>
          </div>
        </div>

        {/* Trades */}
        <div className="p-6 rounded-2xl shadow bg-white border border-zinc-200">
          <div className="text-sm text-zinc-500 font-medium mb-1">
            Total Trades
          </div>
          <div className="text-3xl font-bold text-zinc-900">{trades}</div>
          <div className="text-sm text-zinc-500 mt-1">
            Win Rate: {winRate.toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Secondary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* AI Signal */}
        <div className="p-6 rounded-2xl shadow bg-white border border-zinc-200">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-zinc-700">
              AI Signal (60s)
            </h3>
            <span className="text-xs text-zinc-500">
              {ai?.symbol || "BTCUSDT"}
            </span>
          </div>
          {ai ? (
            <div className="space-y-3">
              {/* Current Price & Target */}
              <div className="flex items-center justify-between p-3 bg-zinc-50 rounded-lg">
                <div>
                  <div className="text-xs text-zinc-500 mb-1">
                    Current Price
                  </div>
                  <div className="text-lg font-bold text-zinc-900">
                    ${(ai._current_price || 0).toLocaleString()}
                  </div>
                </div>
                <div className="text-zinc-300">→</div>
                <div>
                  <div className="text-xs text-zinc-500 mb-1">Price Target</div>
                  <div
                    className={`text-lg font-bold ${
                      (ai.price_target || 0) > (ai._current_price || 0)
                        ? "text-emerald-600"
                        : "text-rose-600"
                    }`}
                  >
                    ${(ai.price_target || 0).toLocaleString()}
                  </div>
                </div>
              </div>

              {/* Probability */}
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-zinc-900">
                  {Math.round((ai.prob_up || 0) * 100)}%
                </span>
                <span className="text-lg text-zinc-600">
                  ↑ {ai.side || "flat"}
                </span>
              </div>

              {/* Confidence Bar */}
              <div className="flex items-center gap-2">
                <div className="flex-1 h-2 bg-zinc-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-emerald-500 transition-all"
                    style={{ width: `${(ai.prob_up || 0) * 100}%` }}
                  />
                </div>
                <span className="text-xs text-zinc-500">
                  Confidence: {((ai.confidence || 0) * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          ) : (
            <div className="text-zinc-400">Loading AI prediction...</div>
          )}
        </div>

        {/* Positions */}
        <div className="p-6 rounded-2xl shadow bg-white border border-zinc-200">
          <div className="text-sm font-semibold text-zinc-700 mb-3">
            Open Positions
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-zinc-900">{openPos}</span>
            <span className="text-sm text-zinc-500">active</span>
          </div>
          <div className="mt-3 text-sm text-zinc-600">
            Cash Balance: ${stats.cash_balance?.toFixed(2) || "0.00"}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="p-6 rounded-2xl shadow bg-zinc-50 border border-zinc-200">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-zinc-700">Quick Stats</h3>
          <div className="flex items-center gap-2 text-xs">
            <span className="flex items-center gap-1 text-emerald-600">
              <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>
              Live Trading
            </span>
            <span className="text-zinc-400">|</span>
            <span className="text-zinc-600">
              {runningEngines.length} Engines Running
            </span>
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
          <div>
            <div className="text-zinc-500">Starting Balance</div>
            <div className="font-semibold text-zinc-900">
              ${stats.starting_balance?.toFixed(2) || "1000.00"}
            </div>
          </div>
          <div>
            <div className="text-zinc-500">Winning Trades</div>
            <div className="font-semibold text-emerald-600">
              {stats.winning_trades || 0}
            </div>
          </div>
          <div>
            <div className="text-zinc-500">Losing Trades</div>
            <div className="font-semibold text-rose-600">
              {stats.losing_trades || 0}
            </div>
          </div>
          <div>
            <div className="text-zinc-500">Profit Factor</div>
            <div className="font-semibold text-zinc-900">
              {stats.profit_factor?.toFixed(2) || "0.00"}
            </div>
          </div>
          <div>
            <div className="text-zinc-500">Active Symbols</div>
            <div className="font-semibold text-blue-600">
              {runningEngines.length > 0
                ? runningEngines
                    .map((e: any) => e.symbol.split("/")[0])
                    .join(", ")
                : "None"}
            </div>
          </div>
        </div>
      </div>

      {/* Model Selector */}
      <ModelSelector />

      {/* Recent Predictions */}
      <RecentPreds />

      {/* Technical Analysis Link */}
      <div className="p-6 rounded-2xl shadow bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-blue-900 mb-2">
              📈 Technical Analysis
            </h3>
            <p className="text-blue-700 text-sm">
              Advanced technical indicators, Fibonacci levels, and AI
              predictions
            </p>
          </div>
          <a
            href="/technical"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            Open Analysis →
          </a>
        </div>
      </div>

      {/* Last Signals */}
      <div className="p-6 rounded-2xl shadow bg-white border border-zinc-200">
        <h3 className="text-sm font-semibold text-zinc-700 mb-3">
          📡 Last Signals
        </h3>
        <div className="space-y-2 max-h-80 overflow-auto">
          {signals?.items && signals.items.length > 0 ? (
            signals.items.map((sig, i) => (
              <div
                key={i}
                className="flex items-center justify-between text-sm py-2 px-3 rounded-lg bg-zinc-50 hover:bg-zinc-100 transition-colors"
              >
                <span className="font-mono text-xs text-zinc-500">
                  {new Date(sig.ts * 1000).toLocaleTimeString()}
                </span>
                <span className="font-medium text-zinc-900">{sig.symbol}</span>
                <span
                  className={`font-bold uppercase ${
                    sig.side === "buy" ? "text-emerald-600" : "text-rose-600"
                  }`}
                >
                  {sig.side}
                </span>
                <span className="text-xs text-zinc-500">
                  {Math.round(sig.confidence * 100)}%
                </span>
                <span className="text-xs px-2 py-1 rounded bg-blue-100 text-blue-700">
                  {sig.strategy}
                </span>
              </div>
            ))
          ) : (
            <div className="text-center text-zinc-400 py-8">
              No signals yet. Start trading to see signals here!
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
