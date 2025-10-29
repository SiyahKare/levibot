import { api } from "@/lib/api";
import useSWR from "swr";

interface BollingerBandsCardProps {
  symbol: string;
  timeframe: string;
  period?: number;
  std_dev?: number;
  window?: number;
}

export default function BollingerBandsCard({
  symbol,
  timeframe,
  period = 20,
  std_dev = 2.0,
  window = 100,
}: BollingerBandsCardProps) {
  const { data: bbData, error: bbError } = useSWR(
    `/ta/bollinger?symbol=${symbol}&timeframe=${timeframe}&period=${period}&std_dev=${std_dev}&window=${window}`,
    () => api.ta.bollinger(symbol, timeframe, period, std_dev, window),
    { refreshInterval: 30_000 }
  );

  if (bbError) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          📊 Bollinger Bands
        </h3>
        <div className="text-red-500">Failed to load Bollinger Bands data</div>
      </div>
    );
  }

  if (!bbData) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          📊 Bollinger Bands
        </h3>
        <div className="text-gray-500">Loading Bollinger Bands data...</div>
      </div>
    );
  }

  const getBBStatus = (position: number) => {
    if (position >= 90)
      return {
        status: "Upper Band",
        color: "text-red-500",
        bg: "bg-red-100 dark:bg-red-900",
      };
    if (position <= 10)
      return {
        status: "Lower Band",
        color: "text-green-500",
        bg: "bg-green-100 dark:bg-green-900",
      };
    if (position >= 70)
      return {
        status: "Near Upper",
        color: "text-orange-500",
        bg: "bg-orange-100 dark:bg-orange-900",
      };
    if (position <= 30)
      return {
        status: "Near Lower",
        color: "text-blue-500",
        bg: "bg-blue-100 dark:bg-blue-900",
      };
    return {
      status: "Middle",
      color: "text-gray-500",
      bg: "bg-gray-100 dark:bg-gray-700",
    };
  };

  const bbStatus = getBBStatus(bbData.position);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        📊 Bollinger Bands
      </h3>

      <div className="space-y-4">
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600 dark:text-gray-400">
              Upper Band
            </span>
            <span className="text-sm font-medium text-red-500">
              ${bbData.upper_band.toLocaleString()}
            </span>
          </div>

          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600 dark:text-gray-400">
              Middle Band (SMA)
            </span>
            <span className="text-sm font-medium text-gray-900 dark:text-white">
              ${bbData.middle_band.toLocaleString()}
            </span>
          </div>

          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600 dark:text-gray-400">
              Lower Band
            </span>
            <span className="text-sm font-medium text-green-500">
              ${bbData.lower_band.toLocaleString()}
            </span>
          </div>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Current Price
          </span>
          <span className="text-lg font-bold text-gray-900 dark:text-white">
            ${bbData.current_price.toLocaleString()}
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Position
          </span>
          <span
            className={`px-3 py-1 rounded-full text-sm font-medium ${bbStatus.color} ${bbStatus.bg}`}
          >
            {bbStatus.status} ({bbData.position.toFixed(1)}%)
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Band Width
          </span>
          <span className="text-sm font-medium text-gray-900 dark:text-white">
            {bbData.width.toFixed(2)}%
          </span>
        </div>

        {/* Bollinger Bands Visualization */}
        <div className="space-y-2">
          <div className="text-xs text-gray-600 dark:text-gray-400 text-center">
            Price Position in Bands
          </div>
          <div className="relative h-8 bg-gray-100 dark:bg-gray-700 rounded-lg overflow-hidden">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full h-1 bg-gradient-to-r from-green-500 via-yellow-500 to-red-500 rounded-full" />
            </div>
            <div
              className="absolute top-0 w-1 h-full bg-gray-900 dark:bg-white rounded-full"
              style={{ left: `${bbData.position}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400">
            <span>Lower</span>
            <span>Middle</span>
            <span>Upper</span>
          </div>
        </div>

        {/* Parameters */}
        <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
          <div className="grid grid-cols-2 gap-2 text-xs text-gray-600 dark:text-gray-400">
            <div className="text-center">
              <div className="font-medium">Period</div>
              <div>{bbData.period}</div>
            </div>
            <div className="text-center">
              <div className="font-medium">Std Dev</div>
              <div>{bbData.std_dev}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


