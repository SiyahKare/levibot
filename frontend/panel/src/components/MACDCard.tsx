import { api } from "@/lib/api";
import useSWR from "swr";

interface MACDCardProps {
  symbol: string;
  timeframe: string;
  fast?: number;
  slow?: number;
  signal?: number;
  window?: number;
}

export default function MACDCard({
  symbol,
  timeframe,
  fast = 12,
  slow = 26,
  signal = 9,
  window = 100,
}: MACDCardProps) {
  const { data: macdData, error: macdError } = useSWR(
    `/ta/macd?symbol=${symbol}&timeframe=${timeframe}&fast=${fast}&slow=${slow}&signal=${signal}&window=${window}`,
    () => api.ta.macd(symbol, timeframe, fast, slow, signal, window),
    { refreshInterval: 30_000 }
  );

  if (macdError) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          📈 MACD (Moving Average Convergence Divergence)
        </h3>
        <div className="text-red-500">Failed to load MACD data</div>
      </div>
    );
  }

  if (!macdData) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          📈 MACD (Moving Average Convergence Divergence)
        </h3>
        <div className="text-gray-500">Loading MACD data...</div>
      </div>
    );
  }

  const getMACDSignal = (macd: number, signal: number, histogram: number) => {
    if (macd > signal && histogram > 0)
      return {
        signal: "Bullish",
        color: "text-green-500",
        bg: "bg-green-100 dark:bg-green-900",
      };
    if (macd < signal && histogram < 0)
      return {
        signal: "Bearish",
        color: "text-red-500",
        bg: "bg-red-100 dark:bg-red-900",
      };
    if (histogram > 0)
      return {
        signal: "Neutral Bullish",
        color: "text-blue-500",
        bg: "bg-blue-100 dark:bg-blue-900",
      };
    return {
      signal: "Neutral Bearish",
      color: "text-orange-500",
      bg: "bg-orange-100 dark:bg-orange-900",
    };
  };

  const macdSignal = getMACDSignal(
    macdData.macd,
    macdData.signal_line,
    macdData.histogram
  );

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        📈 MACD (Moving Average Convergence Divergence)
      </h3>

      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600 dark:text-gray-400">
              MACD Line
            </span>
            <span
              className={`text-lg font-bold ${
                macdData.macd >= 0 ? "text-green-500" : "text-red-500"
              }`}
            >
              {macdData.macd.toFixed(4)}
            </span>
          </div>

          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600 dark:text-gray-400">
              Signal Line
            </span>
            <span
              className={`text-lg font-bold ${
                macdData.signal_line >= 0 ? "text-green-500" : "text-red-500"
              }`}
            >
              {macdData.signal_line.toFixed(4)}
            </span>
          </div>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Histogram
          </span>
          <span
            className={`text-lg font-bold ${
              macdData.histogram >= 0 ? "text-green-500" : "text-red-500"
            }`}
          >
            {macdData.histogram.toFixed(4)}
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Signal
          </span>
          <span
            className={`px-3 py-1 rounded-full text-sm font-medium ${macdSignal.color} ${macdSignal.bg}`}
          >
            {macdSignal.signal}
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Current Price
          </span>
          <span className="text-sm font-medium text-gray-900 dark:text-white">
            ${macdData.current_price.toLocaleString()}
          </span>
        </div>

        {/* MACD Parameters */}
        <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
          <div className="grid grid-cols-3 gap-2 text-xs text-gray-600 dark:text-gray-400">
            <div className="text-center">
              <div className="font-medium">Fast</div>
              <div>{macdData.fast}</div>
            </div>
            <div className="text-center">
              <div className="font-medium">Slow</div>
              <div>{macdData.slow}</div>
            </div>
            <div className="text-center">
              <div className="font-medium">Signal</div>
              <div>{macdData.signal}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


