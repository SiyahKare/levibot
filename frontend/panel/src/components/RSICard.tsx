import { api } from "@/lib/api";
import useSWR from "swr";

interface RSICardProps {
  symbol: string;
  timeframe: string;
  period?: number;
  window?: number;
}

export default function RSICard({
  symbol,
  timeframe,
  period = 14,
  window = 100,
}: RSICardProps) {
  const { data: rsiData, error: rsiError } = useSWR(
    `/ta/rsi?symbol=${symbol}&timeframe=${timeframe}&period=${period}&window=${window}`,
    () => api.ta.rsi(symbol, timeframe, period, window),
    { refreshInterval: 30_000 }
  );

  if (rsiError) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          📊 RSI (Relative Strength Index)
        </h3>
        <div className="text-red-500">Failed to load RSI data</div>
      </div>
    );
  }

  if (!rsiData) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          📊 RSI (Relative Strength Index)
        </h3>
        <div className="text-gray-500">Loading RSI data...</div>
      </div>
    );
  }

  const getRSIStatus = (rsi: number) => {
    if (rsi >= 70)
      return {
        status: "Overbought",
        color: "text-red-500",
        bg: "bg-red-100 dark:bg-red-900",
      };
    if (rsi <= 30)
      return {
        status: "Oversold",
        color: "text-green-500",
        bg: "bg-green-100 dark:bg-green-900",
      };
    if (rsi >= 50)
      return {
        status: "Bullish",
        color: "text-blue-500",
        bg: "bg-blue-100 dark:bg-blue-900",
      };
    return {
      status: "Bearish",
      color: "text-orange-500",
      bg: "bg-orange-100 dark:bg-orange-900",
    };
  };

  const rsiStatus = getRSIStatus(rsiData.rsi);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        📊 RSI (Relative Strength Index)
      </h3>

      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Current RSI
          </span>
          <span className={`text-2xl font-bold ${rsiStatus.color}`}>
            {rsiData.rsi}
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Status
          </span>
          <span
            className={`px-3 py-1 rounded-full text-sm font-medium ${rsiStatus.color} ${rsiStatus.bg}`}
          >
            {rsiStatus.status}
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Period
          </span>
          <span className="text-sm font-medium text-gray-900 dark:text-white">
            {rsiData.period}
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Current Price
          </span>
          <span className="text-sm font-medium text-gray-900 dark:text-white">
            ${rsiData.current_price.toLocaleString()}
          </span>
        </div>

        {/* RSI Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400">
            <span>0</span>
            <span>30</span>
            <span>50</span>
            <span>70</span>
            <span>100</span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all duration-300 ${
                rsiData.rsi >= 70
                  ? "bg-red-500"
                  : rsiData.rsi <= 30
                  ? "bg-green-500"
                  : rsiData.rsi >= 50
                  ? "bg-blue-500"
                  : "bg-orange-500"
              }`}
              style={{ width: `${rsiData.rsi}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}


