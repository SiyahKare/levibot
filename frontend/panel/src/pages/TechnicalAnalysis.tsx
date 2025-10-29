/**
 * Technical Analysis Page
 * Comprehensive technical analysis tools and indicators
 */
import BollingerBandsCard from "@/components/BollingerBandsCard";
import MACDCard from "@/components/MACDCard";
import RSICard from "@/components/RSICard";
import { api } from "@/lib/api";
import { useState } from "react";
import useSWR from "swr";

interface TechnicalAnalysisProps {}

export default function TechnicalAnalysis() {
  const [selectedSymbol, setSelectedSymbol] = useState("BTCUSDT");
  const [selectedTimeframe, setSelectedTimeframe] = useState("1m");
  const [selectedWindow, setSelectedWindow] = useState(2880);

  // Fetch Fibonacci data
  const { data: fibData, error: fibError } = useSWR(
    `/ta/fibonacci?symbol=${selectedSymbol}&timeframe=${selectedTimeframe}&window=${selectedWindow}`,
    () => api.ta.fibonacci(selectedSymbol, selectedTimeframe, selectedWindow),
    { refreshInterval: 30_000 }
  );

  // Fetch Fibonacci zone data
  const { data: fibZoneData, error: fibZoneError } = useSWR(
    `/ta/fibonacci/zone?symbol=${selectedSymbol}&timeframe=${selectedTimeframe}&window=${selectedWindow}`,
    () =>
      api.ta.fibonacciZone(selectedSymbol, selectedTimeframe, selectedWindow),
    { refreshInterval: 30_000 }
  );

  // AI prediction data from real API
  const { data: aiData, error: aiError } = useSWR(
    `/ai/predict?symbol=${selectedSymbol}&timeframe=60s&horizon=5`,
    async () => {
      try {
        const result = await api.ai.predict(selectedSymbol, "60s", 5);
        return result;
      } catch (error) {
        console.error("❌ AI predict error:", error);
        throw error;
      }
    },
    { refreshInterval: 30_000 }
  );

  const symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "ADAUSDT", "DOTUSDT"];
  const timeframes = ["1m", "5m", "15m", "1h", "4h", "1d"];
  const windows = [1440, 2880, 4320, 7200]; // 1d, 2d, 3d, 5d

  const getZoneColor = (bias: string) => {
    switch (bias) {
      case "oversold":
        return "text-emerald-600 bg-emerald-50";
      case "overbought":
        return "text-rose-600 bg-rose-50";
      case "neutral":
        return "text-blue-600 bg-blue-50";
      default:
        return "text-zinc-600 bg-zinc-50";
    }
  };

  const getDistColor = (dist: number) => {
    if (dist > 0.001) return "text-emerald-600";
    if (dist < -0.001) return "text-rose-600";
    return "text-yellow-600";
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-zinc-900">
          📊 Technical Analysis
        </h1>
        <div className="text-sm text-zinc-500">
          Real-time market analysis and indicators
        </div>
      </div>

      {/* Controls */}
      <div className="p-6 rounded-2xl shadow bg-white border border-zinc-200">
        <h3 className="text-sm font-semibold text-zinc-700 mb-4">
          Analysis Parameters
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Symbol Selection */}
          <div>
            <label className="block text-xs text-zinc-500 mb-2">Symbol</label>
            <select
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value)}
              className="w-full px-3 py-2 border border-zinc-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {symbols.map((symbol) => (
                <option key={symbol} value={symbol}>
                  {symbol}
                </option>
              ))}
            </select>
          </div>

          {/* Timeframe Selection */}
          <div>
            <label className="block text-xs text-zinc-500 mb-2">
              Timeframe
            </label>
            <select
              value={selectedTimeframe}
              onChange={(e) => setSelectedTimeframe(e.target.value)}
              className="w-full px-3 py-2 border border-zinc-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {timeframes.map((tf) => (
                <option key={tf} value={tf}>
                  {tf}
                </option>
              ))}
            </select>
          </div>

          {/* Window Selection */}
          <div>
            <label className="block text-xs text-zinc-500 mb-2">
              Window (bars)
            </label>
            <select
              value={selectedWindow}
              onChange={(e) => setSelectedWindow(Number(e.target.value))}
              className="w-full px-3 py-2 border border-zinc-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {windows.map((window) => (
                <option key={window} value={window}>
                  {window} bars ({Math.round(window / 1440)}d)
                </option>
              ))}
            </select>
          </div>

          {/* Refresh Button */}
          <div className="flex items-end">
            <button
              onClick={() => window.location.reload()}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
            >
              🔄 Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Main Analysis Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Fibonacci Retracement */}
        <div className="p-6 rounded-2xl shadow bg-white border border-zinc-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-zinc-700">
              🎯 Fibonacci Retracement
            </h3>
            {fibZoneData && (
              <span
                className={`px-3 py-1 rounded-full text-xs font-medium ${getZoneColor(
                  fibZoneData.bias
                )}`}
              >
                {fibZoneData.bias.toUpperCase()}
              </span>
            )}
          </div>

          {fibError ? (
            <div className="text-red-500 text-sm">
              Failed to load Fibonacci data: {fibError.message}
            </div>
          ) : !fibData ? (
            <div className="text-zinc-400">Loading Fibonacci data...</div>
          ) : (
            <div className="space-y-4">
              {/* Price Levels */}
              <div className="grid grid-cols-3 text-center text-sm">
                <div>
                  <div className="text-zinc-500">Swing High</div>
                  <div className="font-semibold text-zinc-900">
                    ${fibData.swing_high.toLocaleString()}
                  </div>
                </div>
                <div>
                  <div className="text-zinc-500">Current Price</div>
                  <div className="font-bold text-blue-600">
                    ${fibData.last_close.toLocaleString()}
                  </div>
                </div>
                <div>
                  <div className="text-zinc-500">Swing Low</div>
                  <div className="font-semibold text-zinc-900">
                    ${fibData.swing_low.toLocaleString()}
                  </div>
                </div>
              </div>

              {/* Fibonacci Levels */}
              <div className="space-y-2">
                {Object.entries(fibData.levels).map(([level, price]) => {
                  const dist = fibData.dist[level];
                  const isGoldenRatio = level === "0.618";
                  return (
                    <div
                      key={level}
                      className={`flex justify-between items-center text-sm py-2 px-3 rounded-lg ${
                        isGoldenRatio
                          ? "bg-yellow-50 border border-yellow-200"
                          : "bg-zinc-50"
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs text-zinc-500">
                          {level}
                        </span>
                        {isGoldenRatio && (
                          <span className="text-yellow-600">🌟</span>
                        )}
                      </div>
                      <div className="font-semibold text-zinc-900">
                        ${price.toLocaleString()}
                      </div>
                      <div
                        className={`font-mono text-xs ${getDistColor(dist)}`}
                      >
                        {dist > 0 ? "+" : ""}
                        {(dist * 100).toFixed(2)}%
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Analysis Summary */}
              <div className="pt-4 border-t border-zinc-200">
                <div className="text-xs text-zinc-500">
                  Analysis: {selectedSymbol} • {selectedTimeframe} •{" "}
                  {selectedWindow} bars
                </div>
                <div className="text-xs text-zinc-400">
                  Updated: {new Date(fibData.ts).toLocaleTimeString()}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* AI Prediction */}
        <div className="p-6 rounded-2xl shadow bg-white border border-zinc-200">
          <h3 className="text-lg font-semibold text-zinc-700 mb-4">
            🤖 AI Prediction
          </h3>

          {aiError ? (
            <div className="text-red-500 text-sm">
              Failed to load AI prediction: {aiError.message}
            </div>
          ) : !aiData ? (
            <div className="text-zinc-400">Loading AI prediction...</div>
          ) : (
            <div className="space-y-4">
              {/* Current Price & Target */}
              <div className="flex items-center justify-between p-4 bg-zinc-50 rounded-lg">
                <div>
                  <div className="text-xs text-zinc-500 mb-1">
                    Current Price
                  </div>
                  <div className="text-xl font-bold text-zinc-900">
                    ${(aiData._current_price || 0).toLocaleString()}
                  </div>
                </div>
                <div className="text-zinc-300 text-2xl">→</div>
                <div>
                  <div className="text-xs text-zinc-500 mb-1">Price Target</div>
                  <div
                    className={`text-xl font-bold ${
                      (aiData.price_target || 0) > (aiData._current_price || 0)
                        ? "text-emerald-600"
                        : "text-rose-600"
                    }`}
                  >
                    ${(aiData.price_target || 0).toLocaleString()}
                  </div>
                </div>
              </div>

              {/* Probability */}
              <div className="text-center">
                <div className="text-4xl font-bold text-zinc-900 mb-2">
                  {Math.round((aiData.prob_up || 0) * 100)}%
                </div>
                <div className="text-lg text-zinc-600 mb-4">
                  ↑ {aiData.side || "flat"}
                </div>

                {/* Confidence Bar */}
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-3 bg-zinc-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-emerald-500 transition-all"
                      style={{ width: `${(aiData.prob_up || 0) * 100}%` }}
                    />
                  </div>
                  <span className="text-xs text-zinc-500">
                    {((aiData.confidence || 0) * 100).toFixed(0)}%
                  </span>
                </div>
              </div>

              {/* Model Details */}
              <div className="pt-4 border-t border-zinc-200">
                <div className="grid grid-cols-2 gap-4 text-xs">
                  <div>
                    <div className="text-zinc-500">LGBM</div>
                    <div className="font-semibold">
                      {((aiData._prob_lgbm || 0) * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div>
                    <div className="text-zinc-500">TFT</div>
                    <div className="font-semibold">
                      {((aiData._prob_tft || 0) * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div>
                    <div className="text-zinc-500">Sentiment</div>
                    <div className="font-semibold">
                      {((aiData._prob_sent || 0) * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div>
                    <div className="text-zinc-500">Horizon</div>
                    <div className="font-semibold">60s</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Additional Technical Indicators */}
      <div className="space-y-6">
        <h3 className="text-lg font-semibold text-zinc-700 dark:text-white">
          📈 Additional Indicators
        </h3>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <RSICard
            symbol={selectedSymbol}
            timeframe={selectedTimeframe}
            period={14}
            window={100}
          />
          <MACDCard
            symbol={selectedSymbol}
            timeframe={selectedTimeframe}
            fast={12}
            slow={26}
            signal={9}
            window={100}
          />
          <BollingerBandsCard
            symbol={selectedSymbol}
            timeframe={selectedTimeframe}
            period={20}
            std_dev={2.0}
            window={100}
          />
        </div>
      </div>
    </div>
  );
}
