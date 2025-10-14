import { api } from "@/lib/api";
import { useState } from "react";
import { toast } from "sonner";
import useSWR from "swr";

interface Position {
  symbol: string;
  side: string;
  qty: number;
  entry_price: number;
  current_price: number;
  notional: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  opened_at: string;
}

interface Trade {
  id: string;
  symbol: string;
  side: string;
  qty: number;
  entry_price: number;
  exit_price: number;
  pnl_usd: number;
  pnl_pct: number;
  duration_sec: number;
  opened_at: string;
  closed_at: string;
}

export default function PaperPage() {
  const { data: portfolio, mutate: mutatePortfolio } = useSWR(
    "/paper/portfolio",
    () => api.paperPortfolio(),
    { refreshInterval: 5000 }
  );

  const { data: positions } = useSWR(
    "/paper/positions",
    () => api.paperPositions(),
    { refreshInterval: 3000 }
  );

  const { data: trades } = useSWR("/paper/trades", () => api.paperTrades(20), {
    refreshInterval: 10000,
  });

  const [testSymbol, setTestSymbol] = useState("BTCUSDT");
  const [testSide, setTestSide] = useState<"buy" | "sell">("buy");
  const [testNotional, setTestNotional] = useState(100);
  const [aiLoading, setAiLoading] = useState(false);

  // AI Prediction
  const { data: aiPrediction } = useSWR(
    `/ai/predict/${testSymbol}`,
    () => api.aiPredict(testSymbol, "60s"),
    { refreshInterval: 30000 } // 30s refresh
  );

  const handleTestTrade = async () => {
    try {
      await api.paperTestTrade(testSymbol, testSide, testNotional);
      toast.success(`Test ${testSide} placed!`);
      mutatePortfolio();
    } catch (e: any) {
      toast.error(e.message || "Trade failed");
    }
  };

  const handleAITrade = async () => {
    if (!aiPrediction?.ok || !aiPrediction?.prob_up) {
      toast.error("No AI signal available");
      return;
    }

    setAiLoading(true);
    try {
      const side = aiPrediction.prob_up >= 0.5 ? "buy" : "sell";
      await api.paperTestTrade(testSymbol, side, testNotional);
      toast.success(`AI ${side} executed!`);
      mutatePortfolio();
    } catch (e: any) {
      toast.error(e.message || "AI trade failed");
    } finally {
      setAiLoading(false);
    }
  };

  // Derived AI signals from prob_up
  const aiSignal = aiPrediction?.prob_up
    ? aiPrediction.prob_up >= 0.55
      ? "buy"
      : aiPrediction.prob_up <= 0.45
      ? "sell"
      : "hold"
    : null;

  const aiPredictedChange = aiPrediction?.prob_up
    ? (aiPrediction.prob_up - 0.5) * 2 // -1 to +1 range
    : 0;

  const stats = portfolio || {};
  const positionsList: Position[] = positions?.positions || [];
  const tradesList: Trade[] = trades?.trades || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-zinc-900">📄 Paper Trading</h1>
        <div className="flex items-center gap-2 text-sm text-zinc-600">
          <span
            className={`inline-flex items-center gap-1 px-2 py-1 rounded ${
              stats.ok
                ? "bg-emerald-50 text-emerald-700"
                : "bg-rose-50 text-rose-700"
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                stats.ok ? "bg-emerald-500" : "bg-rose-500"
              }`}
            />
            {stats.ok ? "Active" : "Error"}
          </span>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border bg-white">
          <div className="text-sm text-zinc-600 mb-1">Cash Balance</div>
          <div className="text-2xl font-bold text-zinc-900">
            $
            {stats.cash_balance?.toLocaleString("en-US", {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            }) || "0.00"}
          </div>
          <div className="text-xs text-zinc-500 mt-1">
            Start: ${stats.starting_balance?.toLocaleString() || "0"}
          </div>
        </div>

        <div className="p-4 rounded-xl border bg-white">
          <div className="text-sm text-zinc-600 mb-1">Total Equity</div>
          <div className="text-2xl font-bold text-zinc-900">
            $
            {stats.total_equity?.toLocaleString("en-US", {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            }) || "0.00"}
          </div>
          <div className="text-xs text-zinc-500 mt-1">
            Cash + Unrealized PnL
          </div>
        </div>

        <div className="p-4 rounded-xl border bg-white">
          <div className="text-sm text-zinc-600 mb-1">Total PnL</div>
          <div
            className={`text-2xl font-bold ${
              (stats.total_pnl || 0) >= 0 ? "text-emerald-600" : "text-rose-600"
            }`}
          >
            {(stats.total_pnl || 0) >= 0 ? "+" : ""}$
            {stats.total_pnl?.toLocaleString("en-US", {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            }) || "0.00"}
          </div>
          <div className="text-xs text-zinc-500 mt-1">
            {(
              ((stats.total_pnl || 0) / (stats.starting_balance || 1)) *
              100
            ).toFixed(2)}
            % ROI
          </div>
        </div>

        <div className="p-4 rounded-xl border bg-white">
          <div className="text-sm text-zinc-600 mb-1">Win Rate</div>
          <div className="text-2xl font-bold text-zinc-900">
            {stats.win_rate?.toFixed(1) || "0.0"}%
          </div>
          <div className="text-xs text-zinc-500 mt-1">
            {stats.total_trades || 0} trades · PF:{" "}
            {stats.profit_factor?.toFixed(2) || "0.00"}
          </div>
        </div>
      </div>

      {/* AI Recommendation */}
      <div className="p-4 rounded-xl border bg-gradient-to-br from-purple-50 to-pink-50">
        <div className="flex items-center justify-between mb-3">
          <div className="font-medium text-zinc-900">
            🤖 AI Trading Assistant
          </div>
          {aiPrediction?.ok && (
            <span className="text-xs text-zinc-500">
              Updated {new Date().toLocaleTimeString()}
            </span>
          )}
        </div>

        {aiPrediction?.ok ? (
          <div className="space-y-3">
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <div className="text-sm text-zinc-600 mb-1">Signal</div>
                <div
                  className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg font-semibold ${
                    aiSignal === "buy"
                      ? "bg-emerald-100 text-emerald-700"
                      : aiSignal === "sell"
                      ? "bg-rose-100 text-rose-700"
                      : "bg-zinc-100 text-zinc-700"
                  }`}
                >
                  {aiSignal === "buy" && "📈 LONG"}
                  {aiSignal === "sell" && "📉 SHORT"}
                  {aiSignal === "hold" && "⏸️ HOLD"}
                </div>
              </div>
              <div>
                <div className="text-sm text-zinc-600 mb-1">Confidence</div>
                <div className="text-lg font-bold text-zinc-900">
                  {(aiPrediction.confidence * 100).toFixed(1)}%
                </div>
              </div>
              <div>
                <div className="text-sm text-zinc-600 mb-1">Prediction</div>
                <div
                  className={`text-lg font-bold ${
                    aiPredictedChange >= 0
                      ? "text-emerald-600"
                      : "text-rose-600"
                  }`}
                >
                  {aiPredictedChange >= 0 ? "+" : ""}
                  {(aiPredictedChange * 100).toFixed(2)}%
                </div>
              </div>
            </div>

            {aiSignal !== "hold" && (
              <button
                onClick={handleAITrade}
                disabled={aiLoading}
                className={`w-full px-4 py-2 rounded-lg font-medium ${
                  aiSignal === "buy"
                    ? "bg-emerald-600 hover:bg-emerald-700 text-white"
                    : "bg-rose-600 hover:bg-rose-700 text-white"
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {aiLoading
                  ? "Executing..."
                  : `🤖 AI ${aiSignal?.toUpperCase()} $${testNotional}`}
              </button>
            )}
          </div>
        ) : (
          <div className="text-sm text-zinc-500">Loading AI prediction...</div>
        )}
      </div>

      {/* Quick Test Trade */}
      <div className="p-4 rounded-xl border bg-gradient-to-br from-blue-50 to-cyan-50">
        <div className="font-medium text-zinc-900 mb-3">
          🧪 Manual Test Trade
        </div>
        <div className="flex items-center gap-3">
          <input
            type="text"
            value={testSymbol}
            onChange={(e) => setTestSymbol(e.target.value)}
            placeholder="Symbol"
            className="px-3 py-2 border rounded-lg w-32"
          />
          <select
            value={testSide}
            onChange={(e) => setTestSide(e.target.value as "buy" | "sell")}
            className="px-3 py-2 border rounded-lg"
          >
            <option value="buy">Buy</option>
            <option value="sell">Sell</option>
          </select>
          <input
            type="number"
            value={testNotional}
            onChange={(e) => setTestNotional(Number(e.target.value))}
            placeholder="Notional USD"
            className="px-3 py-2 border rounded-lg w-32"
          />
          <button
            onClick={handleTestTrade}
            className={`px-4 py-2 rounded-lg font-medium ${
              testSide === "buy"
                ? "bg-emerald-600 hover:bg-emerald-700 text-white"
                : "bg-rose-600 hover:bg-rose-700 text-white"
            }`}
          >
            {testSide === "buy" ? "📈 Buy" : "📉 Sell"} ${testNotional}
          </button>
        </div>
      </div>

      {/* Open Positions */}
      <div className="rounded-xl border bg-white overflow-hidden">
        <div className="p-4 border-b bg-zinc-50">
          <h2 className="font-semibold text-zinc-900">
            📊 Open Positions ({stats.open_positions || 0})
          </h2>
        </div>
        <div className="overflow-x-auto">
          {positionsList.length === 0 ? (
            <div className="p-8 text-center text-zinc-500">
              No open positions
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-zinc-50 text-xs text-zinc-600 uppercase">
                <tr>
                  <th className="px-4 py-3 text-left">Symbol</th>
                  <th className="px-4 py-3 text-left">Side</th>
                  <th className="px-4 py-3 text-right">Qty</th>
                  <th className="px-4 py-3 text-right">Entry</th>
                  <th className="px-4 py-3 text-right">Current</th>
                  <th className="px-4 py-3 text-right">PnL</th>
                  <th className="px-4 py-3 text-right">PnL %</th>
                  <th className="px-4 py-3 text-left">Opened</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {positionsList.map((pos, idx) => (
                  <tr key={idx} className="hover:bg-zinc-50">
                    <td className="px-4 py-3 font-medium">{pos.symbol}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-medium rounded ${
                          pos.side === "long"
                            ? "bg-emerald-100 text-emerald-700"
                            : "bg-rose-100 text-rose-700"
                        }`}
                      >
                        {pos.side.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-sm">
                      {pos.qty.toFixed(6)}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-sm">
                      ${pos.entry_price.toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-sm">
                      ${pos.current_price?.toLocaleString() || "-"}
                    </td>
                    <td
                      className={`px-4 py-3 text-right font-mono text-sm font-medium ${
                        (pos.unrealized_pnl || 0) >= 0
                          ? "text-emerald-600"
                          : "text-rose-600"
                      }`}
                    >
                      {(pos.unrealized_pnl || 0) >= 0 ? "+" : ""}$
                      {pos.unrealized_pnl?.toFixed(2) || "0.00"}
                    </td>
                    <td
                      className={`px-4 py-3 text-right font-mono text-sm ${
                        (pos.unrealized_pnl_pct || 0) >= 0
                          ? "text-emerald-600"
                          : "text-rose-600"
                      }`}
                    >
                      {(pos.unrealized_pnl_pct || 0) >= 0 ? "+" : ""}
                      {pos.unrealized_pnl_pct?.toFixed(2) || "0.00"}%
                    </td>
                    <td className="px-4 py-3 text-sm text-zinc-600">
                      {new Date(pos.opened_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Recent Trades */}
      <div className="rounded-xl border bg-white overflow-hidden">
        <div className="p-4 border-b bg-zinc-50">
          <h2 className="font-semibold text-zinc-900">
            📜 Recent Trades (Last 20)
          </h2>
        </div>
        <div className="overflow-x-auto">
          {tradesList.length === 0 ? (
            <div className="p-8 text-center text-zinc-500">No trades yet</div>
          ) : (
            <table className="w-full">
              <thead className="bg-zinc-50 text-xs text-zinc-600 uppercase">
                <tr>
                  <th className="px-4 py-3 text-left">Symbol</th>
                  <th className="px-4 py-3 text-left">Side</th>
                  <th className="px-4 py-3 text-right">Qty</th>
                  <th className="px-4 py-3 text-right">Entry</th>
                  <th className="px-4 py-3 text-right">Exit</th>
                  <th className="px-4 py-3 text-right">PnL</th>
                  <th className="px-4 py-3 text-right">PnL %</th>
                  <th className="px-4 py-3 text-right">Duration</th>
                  <th className="px-4 py-3 text-left">Closed</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {tradesList.map((trade, idx) => (
                  <tr key={idx} className="hover:bg-zinc-50">
                    <td className="px-4 py-3 font-medium">{trade.symbol}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-medium rounded ${
                          trade.side === "buy"
                            ? "bg-emerald-100 text-emerald-700"
                            : "bg-rose-100 text-rose-700"
                        }`}
                      >
                        {trade.side.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-sm">
                      {trade.qty.toFixed(6)}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-sm">
                      ${trade.entry_price.toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-sm">
                      ${trade.exit_price.toLocaleString()}
                    </td>
                    <td
                      className={`px-4 py-3 text-right font-mono text-sm font-medium ${
                        trade.pnl_usd >= 0
                          ? "text-emerald-600"
                          : "text-rose-600"
                      }`}
                    >
                      {trade.pnl_usd >= 0 ? "+" : ""}${trade.pnl_usd.toFixed(2)}
                    </td>
                    <td
                      className={`px-4 py-3 text-right font-mono text-sm ${
                        trade.pnl_pct >= 0
                          ? "text-emerald-600"
                          : "text-rose-600"
                      }`}
                    >
                      {trade.pnl_pct >= 0 ? "+" : ""}
                      {trade.pnl_pct.toFixed(2)}%
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-sm text-zinc-600">
                      {(trade.duration_sec / 60).toFixed(1)}m
                    </td>
                    <td className="px-4 py-3 text-sm text-zinc-600">
                      {new Date(trade.closed_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
