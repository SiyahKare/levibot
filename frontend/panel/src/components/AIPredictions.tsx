import { useEffect, useState } from "react";

interface PredictionData {
  should_buy: boolean;
  confidence: number;
  ml_score: number;
  rsi: number | null;
  volatility: number;
  returns: {
    ret_1: number;
    ret_5: number;
    ret_10: number;
  };
}

interface AIPredictionsProps {
  onTrade?: (symbol: string, side: "buy" | "sell") => void;
}

export default function AIPredictions({ onTrade }: AIPredictionsProps) {
  const [predictions, setPredictions] = useState<
    Record<string, PredictionData>
  >({});
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchPredictions = async () => {
    try {
      const res = await fetch("/automation/predictions");
      const data = await res.json();
      if (data.ok) {
        setPredictions(data.predictions);
        setLastUpdate(new Date());
      }
    } catch (e) {
      console.error("Failed to fetch predictions:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPredictions();
    const interval = setInterval(fetchPredictions, 15000); // 15s refresh
    return () => clearInterval(interval);
  }, []);

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.75) return "text-green-400";
    if (confidence >= 0.65) return "text-yellow-400";
    return "text-gray-400";
  };

  const getConfidenceBg = (confidence: number) => {
    if (confidence >= 0.75) return "bg-green-500/20 border-green-500/50";
    if (confidence >= 0.65) return "bg-yellow-500/20 border-yellow-500/50";
    return "bg-gray-500/20 border-gray-500/50";
  };

  const getRsiSignal = (rsi: number | null) => {
    if (!rsi) return { text: "N/A", color: "text-gray-400" };
    if (rsi < 30) return { text: "OVERSOLD 🟢", color: "text-green-400" };
    if (rsi > 70) return { text: "OVERBOUGHT 🔴", color: "text-red-400" };
    return { text: "NEUTRAL", color: "text-gray-400" };
  };

  const getTrendEmoji = (returns: PredictionData["returns"]) => {
    const trend_10 = returns.ret_10;
    if (trend_10 > 0.02) return "📈🔥";
    if (trend_10 > 0.01) return "📈";
    if (trend_10 < -0.02) return "📉💧";
    if (trend_10 < -0.01) return "📉";
    return "➡️";
  };

  if (loading) {
    return (
      <div className="bg-zinc-900 rounded-xl p-6 border border-zinc-800">
        <div className="flex items-center justify-center">
          <svg
            className="animate-spin h-8 w-8 text-blue-500"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            ></circle>
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            ></path>
          </svg>
          <span className="ml-3 text-gray-400">Loading AI predictions...</span>
        </div>
      </div>
    );
  }

  const sortedPredictions = Object.entries(predictions).sort(
    ([, a], [, b]) => b.confidence - a.confidence
  );

  return (
    <div className="bg-zinc-900 rounded-xl p-6 border border-zinc-800 shadow-xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            🧠 AI Predictions
          </h2>
          <p className="text-sm text-gray-400 mt-1">
            Real-time ML-based trading signals
          </p>
        </div>
        {lastUpdate && (
          <div className="text-xs text-gray-500">
            Updated: {lastUpdate.toLocaleTimeString()}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {sortedPredictions.map(([symbol, pred]) => {
          const rsiSignal = getRsiSignal(pred.rsi);
          const trendEmoji = getTrendEmoji(pred.returns);

          return (
            <div
              key={symbol}
              className={`border rounded-lg p-4 transition-all hover:shadow-lg ${getConfidenceBg(
                pred.confidence
              )}`}
            >
              {/* Header */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-xl font-bold text-white">
                    {symbol.replace("USDT", "")}
                  </span>
                  <span className="text-lg">{trendEmoji}</span>
                </div>
                <div className="flex flex-col items-end">
                  <span
                    className={`text-2xl font-bold ${getConfidenceColor(
                      pred.confidence
                    )}`}
                  >
                    {(pred.confidence * 100).toFixed(0)}%
                  </span>
                  <span className="text-xs text-gray-400">Confidence</span>
                </div>
              </div>

              {/* Recommendation */}
              <div className="mb-3">
                {pred.should_buy ? (
                  <div className="bg-green-500/20 border border-green-500/50 rounded-lg px-3 py-2 flex items-center justify-between">
                    <span className="text-green-400 font-semibold">
                      🎯 BUY SIGNAL
                    </span>
                    {onTrade && (
                      <button
                        onClick={() => onTrade(symbol, "buy")}
                        className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-sm rounded-lg transition"
                      >
                        Execute
                      </button>
                    )}
                  </div>
                ) : (
                  <div className="bg-gray-500/20 border border-gray-500/50 rounded-lg px-3 py-2">
                    <span className="text-gray-400 font-semibold">
                      ⏸️ NO SIGNAL
                    </span>
                  </div>
                )}
              </div>

              {/* Indicators */}
              <div className="space-y-2 text-sm">
                {/* ML Score */}
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">ML Score:</span>
                  <div className="flex items-center gap-2">
                    <div className="w-24 h-2 bg-zinc-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all"
                        style={{ width: `${pred.ml_score * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-white font-mono">
                      {(pred.ml_score * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>

                {/* RSI */}
                {pred.rsi && (
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400">RSI:</span>
                    <span className={`font-mono ${rsiSignal.color}`}>
                      {pred.rsi.toFixed(1)} - {rsiSignal.text}
                    </span>
                  </div>
                )}

                {/* Volatility */}
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">Volatility:</span>
                  <span className="text-white font-mono">
                    {(pred.volatility * 100).toFixed(2)}%
                  </span>
                </div>

                {/* Returns */}
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">Returns (1/5/10):</span>
                  <div className="flex gap-2 font-mono text-xs">
                    <span
                      className={
                        pred.returns.ret_1 >= 0
                          ? "text-green-400"
                          : "text-red-400"
                      }
                    >
                      {(pred.returns.ret_1 * 100).toFixed(2)}%
                    </span>
                    <span
                      className={
                        pred.returns.ret_5 >= 0
                          ? "text-green-400"
                          : "text-red-400"
                      }
                    >
                      {(pred.returns.ret_5 * 100).toFixed(2)}%
                    </span>
                    <span
                      className={
                        pred.returns.ret_10 >= 0
                          ? "text-green-400"
                          : "text-red-400"
                      }
                    >
                      {(pred.returns.ret_10 * 100).toFixed(2)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {sortedPredictions.length === 0 && (
        <div className="text-center py-8 text-gray-400">
          <p>No predictions available yet.</p>
          <p className="text-sm mt-2">AI engine is collecting price data...</p>
        </div>
      )}
    </div>
  );
}
