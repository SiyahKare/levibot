import { useState } from "react";

interface TradeWidgetProps {
  onTradeSuccess?: () => void;
}

export default function TradeWidget({ onTradeSuccess }: TradeWidgetProps) {
  const [symbol, setSymbol] = useState("BTCUSDT");
  const [notional, setNotional] = useState("100");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  const popularCoins = [
    { symbol: "BTCUSDT", name: "Bitcoin" },
    { symbol: "ETHUSDT", name: "Ethereum" },
    { symbol: "SOLUSDT", name: "Solana" },
    { symbol: "BNBUSDT", name: "BNB" },
    { symbol: "XRPUSDT", name: "XRP" },
    { symbol: "ADAUSDT", name: "Cardano" },
    { symbol: "DOGEUSDT", name: "Dogecoin" },
    { symbol: "MATICUSDT", name: "Polygon" },
    { symbol: "LINKUSDT", name: "Chainlink" },
    { symbol: "UNIUSDT", name: "Uniswap" },
  ];

  const handleTrade = async (side: "buy" | "sell") => {
    setLoading(true);
    setMessage(null);

    try {
      const response = await fetch("/paper/order", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          symbol: symbol,
          side: side,
          notional_usd: parseFloat(notional),
        }),
      });

      const data = await response.json();

      if (data.ok) {
        if (side === "buy") {
          setMessage({
            type: "success",
            text: `✅ Position Opened! ${data.qty.toFixed(4)} ${
              data.symbol
            } @ $${data.price.toFixed(2)}`,
          });
        } else {
          const pnlColor =
            data.pnl_usd >= 0 ? "text-green-400" : "text-red-400";
          setMessage({
            type: "success",
            text: `✅ Position Closed! PnL: ${
              data.pnl_usd >= 0 ? "+" : ""
            }$${data.pnl_usd.toFixed(2)} (${
              data.pnl_pct >= 0 ? "+" : ""
            }${data.pnl_pct.toFixed(2)}%)`,
          });
        }
        if (onTradeSuccess) onTradeSuccess();
      } else {
        setMessage({
          type: "error",
          text: `❌ Error: ${data.error || "Trade failed"}`,
        });
      }
    } catch (error) {
      setMessage({
        type: "error",
        text: `❌ Network error: ${error}`,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-gradient-to-br from-zinc-900 to-zinc-800 rounded-xl p-6 shadow-2xl border border-zinc-700">
      <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
        <span className="text-3xl">⚡</span>
        Quick Trade
      </h2>

      {/* Symbol Selection */}
      <div className="mb-4">
        <label className="block text-sm font-semibold text-gray-400 mb-2">
          Symbol
        </label>
        <select
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          className="w-full bg-zinc-800 text-white border border-zinc-600 rounded-lg px-4 py-3 focus:outline-none focus:border-blue-500 transition"
        >
          {popularCoins.map((coin) => (
            <option key={coin.symbol} value={coin.symbol}>
              {coin.name} ({coin.symbol})
            </option>
          ))}
        </select>
      </div>

      {/* Notional Amount */}
      <div className="mb-6">
        <label className="block text-sm font-semibold text-gray-400 mb-2">
          Amount (USD)
        </label>
        <input
          type="number"
          value={notional}
          onChange={(e) => setNotional(e.target.value)}
          className="w-full bg-zinc-800 text-white border border-zinc-600 rounded-lg px-4 py-3 focus:outline-none focus:border-blue-500 transition"
          placeholder="100"
          min="10"
          max="500"
        />
        <div className="flex gap-2 mt-2">
          {[25, 50, 100, 200].map((amount) => (
            <button
              key={amount}
              onClick={() => setNotional(String(amount))}
              className="flex-1 bg-zinc-700 hover:bg-zinc-600 text-white rounded-lg py-2 text-sm transition"
            >
              ${amount}
            </button>
          ))}
        </div>
      </div>

      {/* Trade Buttons */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <button
          onClick={() => handleTrade("buy")}
          disabled={loading}
          className={`py-4 rounded-lg font-bold text-lg transition shadow-lg ${
            loading
              ? "bg-gray-600 cursor-not-allowed"
              : "bg-gradient-to-r from-green-600 to-green-700 hover:from-green-500 hover:to-green-600 text-white"
          }`}
        >
          {loading ? "⏳" : "📈"} BUY
        </button>
        <button
          onClick={() => handleTrade("sell")}
          disabled={loading}
          className={`py-4 rounded-lg font-bold text-lg transition shadow-lg ${
            loading
              ? "bg-gray-600 cursor-not-allowed"
              : "bg-gradient-to-r from-red-600 to-red-700 hover:from-red-500 hover:to-red-600 text-white"
          }`}
        >
          {loading ? "⏳" : "📉"} SELL
        </button>
      </div>

      {/* Message */}
      {message && (
        <div
          className={`p-4 rounded-lg ${
            message.type === "success"
              ? "bg-green-900/50 border border-green-700 text-green-200"
              : "bg-red-900/50 border border-red-700 text-red-200"
          }`}
        >
          {message.text}
        </div>
      )}

      {/* Info */}
      <div className="mt-4 p-3 bg-blue-900/30 border border-blue-700 rounded-lg">
        <p className="text-xs text-blue-200">
          💡 <strong>BUY</strong> opens a position with real CoinGecko prices.{" "}
          <strong>SELL</strong> closes it and calculates PnL automatically.
        </p>
      </div>
    </div>
  );
}
