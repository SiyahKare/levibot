interface SignalCardProps {
  symbol: string;
  modelTitle: string;
  p_up: number;
  confidence: number;
  extra?: {
    auc?: number;
    brier?: number;
    mu?: number;
    uncertainty?: number;
  };
}

export default function SignalCard({
  symbol,
  modelTitle,
  p_up,
  confidence,
  extra,
}: SignalCardProps) {
  const direction = p_up > 0.5 ? "UP" : "DOWN";
  const directionColor = p_up > 0.5 ? "text-green-400" : "text-red-400";
  const confColor =
    confidence > 0.7
      ? "text-green-400"
      : confidence > 0.4
      ? "text-amber-400"
      : "text-gray-400";

  return (
    <div className="rounded-lg border border-zinc-700 bg-zinc-800/50 p-4 shadow-md">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h4 className="text-sm font-semibold text-gray-300">{modelTitle}</h4>
          <p className="text-xs text-gray-500">{symbol}</p>
        </div>
        <div className={`text-2xl font-bold ${directionColor}`}>
          {direction}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <p className="text-gray-500">p_up</p>
          <p className="font-mono font-bold text-white">
            {(p_up * 100).toFixed(1)}%
          </p>
        </div>
        <div>
          <p className="text-gray-500">confidence</p>
          <p className={`font-mono font-bold ${confColor}`}>
            {(confidence * 100).toFixed(1)}%
          </p>
        </div>

        {extra?.auc !== undefined && (
          <div>
            <p className="text-gray-500">AUC</p>
            <p className="font-mono text-white">{extra.auc.toFixed(3)}</p>
          </div>
        )}
        {extra?.brier !== undefined && (
          <div>
            <p className="text-gray-500">Brier</p>
            <p className="font-mono text-white">{extra.brier.toFixed(4)}</p>
          </div>
        )}
        {extra?.mu !== undefined && (
          <div>
            <p className="text-gray-500">μ (exp ret)</p>
            <p className="font-mono text-white">
              {(extra.mu * 100).toFixed(2)}%
            </p>
          </div>
        )}
        {extra?.uncertainty !== undefined && (
          <div>
            <p className="text-gray-500">σ (unc.)</p>
            <p className="font-mono text-amber-400">
              {extra.uncertainty.toFixed(3)}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
