import useSWR from "swr";

interface RegimeAdvice {
  regime: string;
  risk_multiplier: number;
  entry_delta: number;
  exit_delta: number;
  reason: string;
}

interface AIRegimeCardProps {
  metrics: any;
}

export default function AIRegimeCard({ metrics }: AIRegimeCardProps) {
  const { data, error, isLoading } = useSWR(
    metrics ? ["/ai/regime", metrics] : null,
    async ([url, m]) => {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(m),
      });
      if (!res.ok) throw new Error("AI regime fetch failed");
      const data = await res.json();
      return data.advice as RegimeAdvice;
    },
    {
      refreshInterval: 30000, // 30s
      revalidateOnFocus: false,
    }
  );

  const regimeColors = {
    trend: "text-green-400 bg-green-500/10 border-green-500",
    neutral: "text-gray-400 bg-gray-500/10 border-gray-500",
    meanrev: "text-blue-400 bg-blue-500/10 border-blue-500",
  };

  const advice = data || {
    regime: "neutral",
    risk_multiplier: 1.0,
    entry_delta: 0.0,
    exit_delta: 0.0,
    reason: "Loading...",
  };

  const regimeColor =
    regimeColors[advice.regime as keyof typeof regimeColors] ||
    regimeColors.neutral;

  return (
    <div className="rounded-xl border border-zinc-700 bg-zinc-800/50 p-6 shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold text-white">🧠 AI Regime</h3>
        {isLoading && (
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
        )}
        {error && <span className="text-xs text-red-400">AI Offline</span>}
      </div>

      <div className="space-y-4">
        {/* Regime Badge */}
        <div
          className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg border-2 ${regimeColor}`}
        >
          <span className="text-2xl">
            {advice.regime === "trend"
              ? "📈"
              : advice.regime === "meanrev"
              ? "🔄"
              : "➡️"}
          </span>
          <span className="font-bold uppercase">{advice.regime}</span>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-3 gap-3 text-sm">
          <div className="rounded-lg bg-zinc-900 p-3">
            <p className="text-gray-400 text-xs mb-1">Risk Multiplier</p>
            <p
              className={`font-bold text-lg ${
                advice.risk_multiplier > 1
                  ? "text-green-400"
                  : advice.risk_multiplier < 1
                  ? "text-red-400"
                  : "text-gray-300"
              }`}
            >
              {advice.risk_multiplier.toFixed(2)}x
            </p>
          </div>

          <div className="rounded-lg bg-zinc-900 p-3">
            <p className="text-gray-400 text-xs mb-1">Entry Δ</p>
            <p
              className={`font-bold text-lg ${
                advice.entry_delta > 0
                  ? "text-green-400"
                  : advice.entry_delta < 0
                  ? "text-red-400"
                  : "text-gray-300"
              }`}
            >
              {advice.entry_delta > 0 ? "+" : ""}
              {(advice.entry_delta * 100).toFixed(1)}%
            </p>
          </div>

          <div className="rounded-lg bg-zinc-900 p-3">
            <p className="text-gray-400 text-xs mb-1">Exit Δ</p>
            <p
              className={`font-bold text-lg ${
                advice.exit_delta < 0
                  ? "text-green-400"
                  : advice.exit_delta > 0
                  ? "text-red-400"
                  : "text-gray-300"
              }`}
            >
              {advice.exit_delta > 0 ? "+" : ""}
              {(advice.exit_delta * 100).toFixed(1)}%
            </p>
          </div>
        </div>

        {/* Reason */}
        <div className="rounded-lg bg-zinc-900 p-3">
          <p className="text-gray-400 text-xs mb-1">AI Analysis</p>
          <p className="text-sm text-gray-300">{advice.reason}</p>
        </div>
      </div>
    </div>
  );
}
