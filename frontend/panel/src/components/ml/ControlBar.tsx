import { useState } from "react";

interface ControlBarProps {
  killSwitchEnabled: boolean;
  canaryFraction: number;
  onKillSwitch: (enabled: boolean) => Promise<void>;
  onCanaryChange: (fraction: number) => Promise<void>;
  onStartMarathon: () => Promise<void>;
  onEvaluate: () => void;
}

export default function ControlBar({
  killSwitchEnabled,
  canaryFraction,
  onKillSwitch,
  onCanaryChange,
  onStartMarathon,
  onEvaluate,
}: ControlBarProps) {
  const [loading, setLoading] = useState<string | null>(null);

  const handleKillSwitch = async () => {
    setLoading("kill");
    try {
      await onKillSwitch(!killSwitchEnabled);
    } finally {
      setLoading(null);
    }
  };

  const handleMarathon = async () => {
    setLoading("marathon");
    try {
      await onStartMarathon();
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="rounded-xl border border-zinc-700 bg-zinc-800/50 p-6 space-y-6">
      <h3 className="text-xl font-bold text-white mb-4">🎛️ Controls</h3>

      {/* Kill Switch */}
      <div className="flex items-center justify-between">
        <div>
          <p className="font-semibold text-white">Kill Switch</p>
          <p className="text-sm text-gray-400">Emergency stop all trading</p>
        </div>
        <button
          onClick={handleKillSwitch}
          disabled={loading !== null}
          className={`px-6 py-3 rounded-lg font-bold transition-all ${
            killSwitchEnabled
              ? "bg-red-600 hover:bg-red-700 text-white"
              : "bg-green-600 hover:bg-green-700 text-white"
          } disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {loading === "kill"
            ? "..."
            : killSwitchEnabled
            ? "🛑 ENABLED"
            : "✅ DISABLED"}
        </button>
      </div>

      {/* Canary Fraction */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="font-semibold text-white">Canary Fraction</label>
          <span className="text-sm font-mono text-gray-400">
            {(canaryFraction * 100).toFixed(0)}%
          </span>
        </div>
        <input
          type="range"
          min="0"
          max="50"
          step="5"
          value={canaryFraction * 100}
          onChange={(e) => onCanaryChange(parseFloat(e.target.value) / 100)}
          className="w-full h-2 bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
        />
        <p className="text-xs text-gray-500 mt-1">
          Percentage of trades using canary model
        </p>
      </div>

      {/* Action Buttons */}
      <div className="grid grid-cols-2 gap-3">
        <button
          onClick={handleMarathon}
          disabled={loading !== null}
          className="px-4 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading === "marathon" ? "Starting..." : "🚀 Start Canary (10%)"}
        </button>
        <button
          onClick={onEvaluate}
          className="px-4 py-3 bg-zinc-700 hover:bg-zinc-600 text-white font-semibold rounded-lg transition-all"
        >
          📊 Evaluate 48h
        </button>
      </div>
    </div>
  );
}
