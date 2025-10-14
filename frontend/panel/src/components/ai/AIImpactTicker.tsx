import { useState } from "react";

interface NewsImpact {
  asset: string;
  event_type: string;
  impact: number;
  horizon: string;
  confidence: number;
}

interface AIImpactTickerProps {
  impacts: NewsImpact[];
}

export default function AIImpactTicker({ impacts }: AIImpactTickerProps) {
  const [expanded, setExpanded] = useState(false);

  const displayImpacts = expanded ? impacts : impacts.slice(0, 5);

  const getImpactColor = (impact: number) => {
    if (impact > 0.5) return "text-green-400 bg-green-500/10";
    if (impact > 0.2) return "text-green-300 bg-green-500/5";
    if (impact < -0.5) return "text-red-400 bg-red-500/10";
    if (impact < -0.2) return "text-red-300 bg-red-500/5";
    return "text-gray-400 bg-gray-500/5";
  };

  const getImpactEmoji = (impact: number) => {
    if (impact > 0.5) return "🚀";
    if (impact > 0.2) return "📈";
    if (impact < -0.5) return "💥";
    if (impact < -0.2) return "📉";
    return "➡️";
  };

  return (
    <div className="rounded-xl border border-zinc-700 bg-zinc-800/50 p-6 shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold text-white">📰 AI Impact Ticker</h3>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-sm text-blue-400 hover:text-blue-300 transition"
        >
          {expanded ? "Collapse" : `Show All (${impacts.length})`}
        </button>
      </div>

      {impacts.length === 0 ? (
        <p className="text-gray-500 text-sm">No recent news impacts</p>
      ) : (
        <div className="space-y-2">
          {displayImpacts.map((item, idx) => (
            <div
              key={idx}
              className={`rounded-lg p-3 border border-zinc-700 ${getImpactColor(
                item.impact
              )}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-xl">{getImpactEmoji(item.impact)}</span>
                  <div>
                    <p className="font-semibold text-sm">
                      {item.asset}{" "}
                      <span className="text-xs text-gray-400">
                        ({item.event_type})
                      </span>
                    </p>
                    <p className="text-xs text-gray-500">{item.horizon}</p>
                  </div>
                </div>

                <div className="text-right">
                  <p className="font-bold">
                    {item.impact > 0 ? "+" : ""}
                    {(item.impact * 100).toFixed(0)}%
                  </p>
                  <p className="text-xs text-gray-500">
                    {(item.confidence * 100).toFixed(0)}% conf
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Histogram */}
      <div className="mt-4 pt-4 border-t border-zinc-700">
        <div className="flex items-end justify-between h-16 gap-1">
          {impacts.slice(0, 10).map((item, idx) => {
            const height = Math.abs(item.impact) * 100;
            const color = item.impact > 0 ? "bg-green-500" : "bg-red-500";
            return (
              <div
                key={idx}
                className="flex-1 flex flex-col justify-end"
                title={`${item.asset}: ${(item.impact * 100).toFixed(0)}%`}
              >
                <div
                  className={`${color} rounded-t`}
                  style={{ height: `${height}%` }}
                />
              </div>
            );
          })}
        </div>
        <p className="text-xs text-gray-500 text-center mt-2">
          Last 10 impacts
        </p>
      </div>
    </div>
  );
}
