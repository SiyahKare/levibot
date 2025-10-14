import { useEffect, useState } from "react";
import AIPredictions from "../components/AIPredictions";
import AIStatus from "../components/AIStatus";
import TradeWidget from "../components/TradeWidget";

interface PortfolioStats {
  starting_balance: number;
  cash_balance: number;
  total_equity: number;
  total_pnl: number;
  total_pnl_pct: number;
  open_positions: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  avg_win: number;
  avg_loss: number;
  profit_factor: number;
}

interface Trade {
  trade_id: string;
  symbol: string;
  side: string;
  qty: number;
  entry_price: number;
  exit_price: number;
  entry_time: string;
  exit_time: string;
  pnl_usd: number;
  pnl_pct: number;
  duration_sec: number;
}

export default function PaperTrading() {
  const [prices, setPrices] = useState<Record<string, number>>({});
  const [portfolio, setPortfolio] = useState<PortfolioStats | null>(null);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [realtimeConnected, setRealtimeConnected] = useState(false);

  // Fetch prices
  const fetchPrices = async () => {
    try {
      const res = await fetch("/prices/batch?symbols=BTC,ETH,SOL,BNB,ADA");
      const data = await res.json();
      if (data.ok && data.prices) {
        setPrices(data.prices);
      }
    } catch (e) {
      console.error("Price error:", e);
    }
  };

  // Fetch portfolio stats
  const fetchPortfolio = async () => {
    try {
      const res = await fetch("/paper/portfolio");
      const data = await res.json();
      if (data.ok) {
        setPortfolio(data);
        setError(null);
      }
    } catch (e) {
      console.error("Portfolio error:", e);
      setError("Portfolio verisi alınamadı");
    }
  };

  // Fetch trades from paper API
  const fetchTrades = async () => {
    try {
      const res = await fetch("/paper/trades?limit=20");
      const data = await res.json();
      if (data.ok && Array.isArray(data.trades)) {
        setTrades(data.trades);
      }
      setLoading(false);
    } catch (e) {
      console.error("Trade error:", e);
      setLoading(false);
    }
  };

  // Refresh all data
  const refreshAll = () => {
    fetchPrices();
    fetchPortfolio();
    fetchTrades();
  };

  useEffect(() => {
    // Initial fetch
    refreshAll();

    // SSE for realtime tick updates
    const tickSource = new EventSource("/stream/ticks");

    tickSource.onopen = () => {
      console.log("✅ Realtime ticks connected");
      setRealtimeConnected(true);
    };

    tickSource.onmessage = (event) => {
      try {
        const tick = JSON.parse(event.data);
        if (tick.symbol && tick.last) {
          setPrices((prev) => ({
            ...prev,
            [tick.symbol]: tick.last,
          }));
        }
      } catch (e) {
        console.error("Tick parse error:", e);
      }
    };

    tickSource.onerror = () => {
      console.warn("⚠️ Realtime ticks disconnected");
      setRealtimeConnected(false);
    };

    // SSE for realtime portfolio updates
    const portfolioSource = new EventSource("/stream/portfolio");

    portfolioSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.balance !== undefined) {
          // Map realtime portfolio format to UI format
          setPortfolio({
            starting_balance: 10000, // TODO: Get from API
            cash_balance: data.balance,
            total_equity: data.equity || data.balance,
            total_pnl: data.balance - 10000,
            total_pnl_pct: ((data.balance - 10000) / 10000) * 100,
            open_positions: data.positions_count || 0,
            total_trades: 0, // Not in realtime feed
            winning_trades: 0,
            losing_trades: 0,
            win_rate: 0,
            avg_win: 0,
            avg_loss: 0,
            profit_factor: 0,
          });
        }
      } catch (e) {
        console.error("Portfolio update error:", e);
      }
    };

    // Set up intervals for fallback
    const priceInterval = setInterval(fetchPrices, 30000); // 30s
    const portfolioInterval = setInterval(fetchPortfolio, 5000); // 5s
    const tradeInterval = setInterval(fetchTrades, 10000); // 10s

    return () => {
      clearInterval(priceInterval);
      clearInterval(portfolioInterval);
      clearInterval(tradeInterval);
      tickSource.close();
      portfolioSource.close();
    };
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-2xl text-gray-400">Yükleniyor...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900 border border-red-700 rounded-xl p-6 m-4">
        <h2 className="text-xl font-bold text-white mb-2">⚠️ Hata</h2>
        <p className="text-red-200">{error}</p>
      </div>
    );
  }

  const stats = portfolio || {
    starting_balance: 10000,
    cash_balance: 10000,
    total_equity: 10000,
    total_pnl: 0,
    total_pnl_pct: 0,
    open_positions: 0,
    total_trades: 0,
    winning_trades: 0,
    losing_trades: 0,
    win_rate: 0,
    avg_win: 0,
    avg_loss: 0,
    profit_factor: 0,
  };

  const handleAITrade = async (symbol: string, side: "buy" | "sell") => {
    try {
      const res = await fetch("/paper/order", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ symbol, side, notional_usd: 100 }),
      });
      const data = await res.json();
      if (data.ok) {
        // Refresh data
        refreshAll();
      }
    } catch (e) {
      console.error("AI trade error:", e);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-900 to-purple-900 rounded-2xl p-6 shadow-xl">
        <h1 className="text-3xl font-bold text-white mb-2">
          🧠 AI-Powered Trading Dashboard
        </h1>
        <p className="text-blue-200">
          Machine Learning + Technical Analysis + Risk Management
        </p>
      </div>

      {/* AI Status */}
      <AIStatus />

      {/* AI Predictions */}
      <AIPredictions onTrade={handleAITrade} />

      {/* Live Prices */}
      <div className="bg-zinc-900 rounded-xl p-6 shadow-lg">
        <h2 className="text-xl font-semibold text-white mb-4">
          📈 Canlı Fiyatlar (CoinGecko)
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {Object.entries(prices).map(([symbol, price]) => (
            <div
              key={symbol}
              className="bg-zinc-800 rounded-lg p-4 border border-zinc-700 hover:border-blue-500 transition"
            >
              <div className="text-sm text-gray-400 mb-1">{symbol}</div>
              <div className="text-2xl font-bold text-white">
                ${typeof price === "number" ? price.toLocaleString() : "N/A"}
              </div>
            </div>
          ))}
          {Object.keys(prices).length === 0 && (
            <div className="col-span-5 text-center text-gray-500 py-4">
              Fiyatlar yükleniyor...
            </div>
          )}
        </div>
      </div>

      {/* Trade Widget */}
      <TradeWidget onTradeSuccess={refreshAll} />

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-zinc-900 rounded-xl p-6 shadow-lg border border-zinc-800">
          <div className="text-sm text-gray-400 uppercase mb-2">Başlangıç</div>
          <div className="text-3xl font-bold text-white">
            ${stats.starting_balance.toLocaleString()}
          </div>
        </div>

        <div className="bg-zinc-900 rounded-xl p-6 shadow-lg border border-zinc-800">
          <div className="text-sm text-gray-400 uppercase mb-2">Equity</div>
          <div className="text-3xl font-bold text-white">
            ${stats.total_equity.toFixed(2)}
          </div>
          <div
            className={`text-sm mt-1 ${
              stats.total_pnl >= 0 ? "text-green-400" : "text-red-400"
            }`}
          >
            {stats.total_pnl >= 0 ? "+" : ""}
            {stats.total_pnl_pct.toFixed(2)}%
          </div>
        </div>

        <div className="bg-zinc-900 rounded-xl p-6 shadow-lg border border-zinc-800">
          <div className="text-sm text-gray-400 uppercase mb-2">Total PnL</div>
          <div
            className={`text-3xl font-bold ${
              stats.total_pnl >= 0 ? "text-green-400" : "text-red-400"
            }`}
          >
            {stats.total_pnl >= 0 ? "+" : ""}${stats.total_pnl.toFixed(2)}
          </div>
        </div>

        <div className="bg-zinc-900 rounded-xl p-6 shadow-lg border border-zinc-800">
          <div className="text-sm text-gray-400 uppercase mb-2">Win Rate</div>
          <div className="text-3xl font-bold text-white">
            {stats.win_rate.toFixed(1)}%
          </div>
          <div className="text-sm text-gray-400 mt-1">
            {stats.winning_trades}W / {stats.losing_trades}L
          </div>
        </div>
      </div>

      {/* Additional Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-zinc-900 rounded-xl p-4 shadow-lg border border-zinc-800">
          <div className="text-xs text-gray-400 uppercase mb-1">
            Total Trades
          </div>
          <div className="text-xl font-bold text-white">
            {stats.total_trades}
          </div>
        </div>

        <div className="bg-zinc-900 rounded-xl p-4 shadow-lg border border-zinc-800">
          <div className="text-xs text-gray-400 uppercase mb-1">Avg Win</div>
          <div className="text-xl font-bold text-green-400">
            ${stats.avg_win.toFixed(2)}
          </div>
        </div>

        <div className="bg-zinc-900 rounded-xl p-4 shadow-lg border border-zinc-800">
          <div className="text-xs text-gray-400 uppercase mb-1">Avg Loss</div>
          <div className="text-xl font-bold text-red-400">
            ${stats.avg_loss.toFixed(2)}
          </div>
        </div>

        <div className="bg-zinc-900 rounded-xl p-4 shadow-lg border border-zinc-800">
          <div className="text-xs text-gray-400 uppercase mb-1">
            Profit Factor
          </div>
          <div className="text-xl font-bold text-blue-400">
            {stats.profit_factor.toFixed(2)}x
          </div>
        </div>
      </div>

      {/* Trade History */}
      <div className="bg-zinc-900 rounded-xl p-6 shadow-lg">
        <h2 className="text-xl font-semibold text-white mb-4">
          📜 Trade History
        </h2>

        {trades.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📊</div>
            <div className="text-xl text-gray-400 mb-2">Henüz trade yok</div>
            <div className="text-sm text-gray-500">
              Test trade göndermek için:
            </div>
            <code className="block mt-2 bg-zinc-800 p-3 rounded text-xs text-green-400">
              curl -X POST "http://localhost:8000/paper/trade" -H "Content-Type:
              application/json" -d '{"{"}
              symbol":"BTCUSDT","side":"buy","qty":0.01,"price":60000{"}"}'
            </code>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-zinc-800">
                  <th className="text-left py-3 px-4 text-gray-400 font-semibold">
                    Zaman
                  </th>
                  <th className="text-left py-3 px-4 text-gray-400 font-semibold">
                    Sembol
                  </th>
                  <th className="text-right py-3 px-4 text-gray-400 font-semibold">
                    Entry
                  </th>
                  <th className="text-right py-3 px-4 text-gray-400 font-semibold">
                    Exit
                  </th>
                  <th className="text-right py-3 px-4 text-gray-400 font-semibold">
                    PnL
                  </th>
                  <th className="text-right py-3 px-4 text-gray-400 font-semibold">
                    Return %
                  </th>
                  <th className="text-right py-3 px-4 text-gray-400 font-semibold">
                    Duration
                  </th>
                </tr>
              </thead>
              <tbody>
                {trades.map((trade, idx) => {
                  const pnl = trade.pnl_usd || 0;
                  const time = new Date(trade.exit_time).toLocaleTimeString();

                  return (
                    <tr
                      key={idx}
                      className="border-b border-zinc-800 hover:bg-zinc-800 transition"
                    >
                      <td className="py-3 px-4 text-gray-400 text-sm">
                        {time}
                      </td>
                      <td className="py-3 px-4 text-white font-mono font-semibold">
                        {trade.symbol}
                      </td>
                      <td className="py-3 px-4 text-right text-gray-300">
                        ${trade.entry_price.toFixed(2)}
                      </td>
                      <td className="py-3 px-4 text-right text-gray-300">
                        ${trade.exit_price.toFixed(2)}
                      </td>
                      <td
                        className={`py-3 px-4 text-right font-bold ${
                          pnl >= 0 ? "text-green-400" : "text-red-400"
                        }`}
                      >
                        {pnl >= 0 ? "+" : ""}${pnl.toFixed(2)}
                      </td>
                      <td
                        className={`py-3 px-4 text-right ${
                          pnl >= 0 ? "text-green-400" : "text-red-400"
                        }`}
                      >
                        {pnl >= 0 ? "+" : ""}
                        {trade.pnl_pct.toFixed(2)}%
                      </td>
                      <td className="py-3 px-4 text-right text-gray-400 text-sm">
                        {trade.duration_sec.toFixed(1)}s
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* System Info */}
      <div className="bg-gradient-to-r from-indigo-900 to-purple-900 rounded-xl p-6 shadow-lg">
        <h3 className="text-lg font-semibold text-white mb-3">
          ℹ️ System Info
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <div className="text-indigo-300 font-semibold mb-1">
              Auto-Refresh
            </div>
            <div className="text-white">
              Portfolio: 5s | Trades: 10s | Prices: 30s
            </div>
          </div>
          <div>
            <div className="text-indigo-300 font-semibold mb-1">
              Price Source
            </div>
            <div className="text-white">CoinGecko API (Real-time)</div>
          </div>
          <div>
            <div className="text-indigo-300 font-semibold mb-1">Mode</div>
            <div className="text-white">Paper Trading (Risk-free)</div>
          </div>
        </div>
        <div className="flex gap-3 mt-4">
          <button
            onClick={() => refreshAll()}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
          >
            ↻ Manual Refresh
          </button>
          <button
            onClick={async () => {
              if (
                confirm("Portfolio'yu sıfırlamak istediğinize emin misiniz?")
              ) {
                try {
                  await fetch("/paper/reset?starting_balance=10000", {
                    method: "POST",
                  });
                  alert("Portfolio sıfırlandı!");
                  refreshAll();
                } catch (e) {
                  alert("Hata: " + e);
                }
              }
            }}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition"
          >
            🔄 Reset Portfolio
          </button>
        </div>
      </div>
    </div>
  );
}
