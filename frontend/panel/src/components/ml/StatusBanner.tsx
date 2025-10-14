interface StatusBannerProps {
  health: {
    ok: boolean;
    staleness_sec?: number;
  };
  ece?: number;
}

export default function StatusBanner({ health, ece }: StatusBannerProps) {
  const isCritical =
    !health.ok || (health.staleness_sec && health.staleness_sec > 1800);
  const isWarning = ece && ece > 0.06;

  if (!isCritical && !isWarning) {
    return (
      <div className="rounded-lg border-2 border-green-500 bg-green-500/10 p-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="text-2xl">✅</div>
          <div>
            <h3 className="font-semibold text-green-400">System Healthy</h3>
            <p className="text-sm text-gray-400">
              All systems operational. Feature staleness:{" "}
              {health.staleness_sec?.toFixed(0) || "N/A"}s
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border-2 border-red-500 bg-red-500/10 p-4 mb-6">
      <div className="flex items-center gap-3">
        <div className="text-2xl">🚨</div>
        <div>
          <h3 className="font-semibold text-red-400">
            {isCritical ? "CRITICAL ALERT" : "WARNING"}
          </h3>
          <ul className="text-sm text-gray-300 mt-1 space-y-1">
            {!health.ok && <li>• Health check failed</li>}
            {health.staleness_sec && health.staleness_sec > 1800 && (
              <li>
                • Feature staleness critical: {health.staleness_sec.toFixed(0)}s
                (threshold: 1800s)
              </li>
            )}
            {isWarning && (
              <li>• ECE degraded: {ece?.toFixed(4)} (&gt; 0.06)</li>
            )}
          </ul>
        </div>
      </div>
    </div>
  );
}
