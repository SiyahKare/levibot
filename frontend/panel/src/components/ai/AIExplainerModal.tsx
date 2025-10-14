import { useState } from "react";

interface Explanation {
  cause: string;
  runbook: string[];
  severity: "low" | "medium" | "high" | "critical";
}

interface AIExplainerModalProps {
  isOpen: boolean;
  onClose: () => void;
  context: any;
}

export default function AIExplainerModal({
  isOpen,
  onClose,
  context,
}: AIExplainerModalProps) {
  const [explanation, setExplanation] = useState<Explanation | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const severityColors = {
    low: "text-blue-400 bg-blue-500/10 border-blue-500",
    medium: "text-yellow-400 bg-yellow-500/10 border-yellow-500",
    high: "text-orange-400 bg-orange-500/10 border-orange-500",
    critical: "text-red-400 bg-red-500/10 border-red-500",
  };

  const fetchExplanation = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/ai/explain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(context),
      });

      if (!res.ok) throw new Error("AI explain failed");

      const data = await res.json();
      setExplanation(data.explanation);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
      <div className="bg-zinc-900 rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto border border-zinc-700 shadow-2xl">
        {/* Header */}
        <div className="sticky top-0 bg-zinc-900 border-b border-zinc-700 p-6">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-white">
              🤖 AI Anomaly Explainer
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition text-2xl"
            >
              ×
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Context Summary */}
          <div className="rounded-lg bg-zinc-800 p-4">
            <h3 className="text-sm font-semibold text-gray-400 mb-2">
              Anomaly Context
            </h3>
            <pre className="text-xs text-gray-300 overflow-x-auto">
              {JSON.stringify(context, null, 2)}
            </pre>
          </div>

          {/* Explain Button */}
          {!explanation && !loading && (
            <button
              onClick={fetchExplanation}
              className="w-full px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold rounded-lg transition"
            >
              🧠 Analyze with AI
            </button>
          )}

          {/* Loading */}
          {loading && (
            <div className="flex items-center justify-center py-8">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
              <p className="ml-3 text-gray-400">AI analyzing...</p>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="rounded-lg bg-red-500/10 border border-red-500 p-4">
              <p className="text-red-400">❌ {error}</p>
            </div>
          )}

          {/* Explanation */}
          {explanation && (
            <div className="space-y-4">
              {/* Severity Badge */}
              <div
                className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg border-2 ${
                  severityColors[explanation.severity]
                }`}
              >
                <span className="font-bold uppercase">
                  {explanation.severity} Severity
                </span>
              </div>

              {/* Cause */}
              <div className="rounded-lg bg-zinc-800 p-4">
                <h3 className="text-sm font-semibold text-gray-400 mb-2">
                  Likely Cause
                </h3>
                <p className="text-gray-200">{explanation.cause}</p>
              </div>

              {/* Runbook */}
              <div className="rounded-lg bg-zinc-800 p-4">
                <h3 className="text-sm font-semibold text-gray-400 mb-3">
                  Suggested Actions
                </h3>
                <ol className="space-y-2">
                  {explanation.runbook.map((step, idx) => (
                    <li key={idx} className="flex items-start gap-3">
                      <span className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-500 text-white text-xs flex items-center justify-center font-bold">
                        {idx + 1}
                      </span>
                      <p className="text-gray-300 flex-1">{step}</p>
                    </li>
                  ))}
                </ol>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-zinc-900 border-t border-zinc-700 p-6">
          <button
            onClick={onClose}
            className="w-full px-6 py-3 bg-zinc-700 hover:bg-zinc-600 text-white font-semibold rounded-lg transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
