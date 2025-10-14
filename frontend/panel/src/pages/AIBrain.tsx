import { useState } from "react";
import useSWR from "swr";

interface NewsScoreResult {
  asset: string;
  event_type: string;
  impact: number;
  horizon: string;
  confidence: number;
  error?: string;
}

interface RegimeAdvice {
  regime: string;
  risk_multiplier: number;
  entry_delta: number;
  exit_delta: number;
  reason: string;
}

interface AnomalyExplanation {
  cause: string;
  runbook: string[];
  severity: string;
}

export default function AIBrain() {
  const [headline, setHeadline] = useState("Bitcoin ETF approval imminent, says SEC chairman");
  const [newsScore, setNewsScore] = useState<NewsScoreResult | null>(null);
  const [newsLoading, setNewsLoading] = useState(false);

  const [regimeAdvice, setRegimeAdvice] = useState<RegimeAdvice | null>(null);
  const [regimeLoading, setRegimeLoading] = useState(false);

  const [anomalyExplain, setAnomalyExplain] = useState<AnomalyExplanation | null>(null);
  const [anomalyLoading, setAnomalyLoading] = useState(false);

  const scoreNews = async () => {
    setNewsLoading(true);
    try {
      const r = await fetch("/ai/news/score", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ headline }),
      });
      const data = await r.json();
      setNewsScore(data);
    } catch (e) {
      console.error("News scoring failed:", e);
      setNewsScore({ 
        asset: "ERROR", 
        event_type: "unknown", 
        impact: 0, 
        horizon: "intra", 
        confidence: 0,
        error: String(e)
      });
    } finally {
      setNewsLoading(false);
    }
  };

  const getRegimeAdvice = async () => {
    setRegimeLoading(true);
    try {
      // Mock metrics for demo
      const mockMetrics = {
        volatility: 0.45,
        trend: 0.12,
        ece: 0.048,
        staleness: 850,
        pnl_1d: 0.023,
        pnl_7d: 0.085,
        sharpe: 1.8,
        max_dd: -0.06,
      };
      const r = await fetch("/ai/regime/advice", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ metrics: mockMetrics }),
      });
      const data = await r.json();
      setRegimeAdvice(data);
    } catch (e) {
      console.error("Regime advice failed:", e);
      setRegimeAdvice({
        regime: "ERROR",
        risk_multiplier: 1.0,
        entry_delta: 0.0,
        exit_delta: 0.0,
        reason: String(e),
      });
    } finally {
      setRegimeLoading(false);
    }
  };

  const explainAnomaly = async () => {
    setAnomalyLoading(true);
    try {
      // Mock anomaly context
      const mockContext = {
        ece: 0.082,
        staleness: 2400,
        pnl_1d: -0.032,
        pnl_7d: -0.045,
        psi: 0.18,
        trades_today: 8,
      };
      const r = await fetch("/ai/anomaly/explain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ context: mockContext }),
      });
      const data = await r.json();
      setAnomalyExplain(data);
    } catch (e) {
      console.error("Anomaly explanation failed:", e);
      setAnomalyExplain({
        cause: `AI analysis failed: ${e}`,
        runbook: ["Check logs", "Verify OpenAI API key", "Contact support"],
        severity: "high",
      });
    } finally {
      setAnomalyLoading(false);
    }
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
          🧠 AI Brain
          <span className="text-sm font-normal text-gray-400 bg-zinc-800 px-3 py-1 rounded-full">
            Powered by OpenAI GPT-4o-mini
          </span>
        </h1>
        <p className="text-gray-400 mt-2">
          AI-powered news analysis, regime detection, and anomaly explanations
        </p>
      </div>

      {/* News Scoring */}
      <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-6">
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          📰 News Impact Scorer
        </h2>
        <p className="text-gray-400 text-sm mb-4">
          Analyze crypto news headlines for market impact using AI
        </p>
        
        <textarea
          className="w-full p-3 bg-zinc-800 rounded-lg border border-zinc-700 text-white placeholder-zinc-500 focus:ring-blue-500 focus:border-blue-500 mb-3"
          rows={3}
          value={headline}
          onChange={(e) => setHeadline(e.target.value)}
          placeholder="Enter a crypto news headline..."
        />
        
        <button
          onClick={scoreNews}
          disabled={newsLoading || !headline.trim()}
          className="px-6 py-2 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white font-semibold rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {newsLoading ? "Analyzing..." : "🎯 Score Impact"}
        </button>

        {newsScore && (
          <div className="mt-4 p-4 bg-zinc-800 rounded-lg border border-zinc-700">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div>
                <div className="text-xs uppercase text-zinc-500">Asset</div>
                <div className="text-lg font-bold text-white">{newsScore.asset}</div>
              </div>
              <div>
                <div className="text-xs uppercase text-zinc-500">Event Type</div>
                <div className="text-sm font-semibold text-zinc-300">{newsScore.event_type}</div>
              </div>
              <div>
                <div className="text-xs uppercase text-zinc-500">Impact</div>
                <div className={`text-lg font-bold ${
                  newsScore.impact > 0.3 ? "text-green-400" : 
                  newsScore.impact < -0.3 ? "text-red-400" : 
                  "text-gray-400"
                }`}>
                  {newsScore.impact > 0 ? "+" : ""}{newsScore.impact.toFixed(2)}
                </div>
              </div>
              <div>
                <div className="text-xs uppercase text-zinc-500">Horizon</div>
                <div className="text-sm font-semibold text-zinc-300">{newsScore.horizon}</div>
              </div>
              <div>
                <div className="text-xs uppercase text-zinc-500">Confidence</div>
                <div className="text-lg font-bold text-cyan-400">
                  {(newsScore.confidence * 100).toFixed(0)}%
                </div>
              </div>
            </div>
            {newsScore.error && (
              <div className="mt-3 text-red-400 text-sm">Error: {newsScore.error}</div>
            )}
          </div>
        )}
      </div>

      {/* Regime Advisor */}
      <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-6">
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          🌡️ Regime Advisor
        </h2>
        <p className="text-gray-400 text-sm mb-4">
          Get AI-powered regime detection and risk parameter recommendations
        </p>
        
        <button
          onClick={getRegimeAdvice}
          disabled={regimeLoading}
          className="px-6 py-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {regimeLoading ? "Analyzing..." : "🔮 Get Regime Advice"}
        </button>

        {regimeAdvice && (
          <div className="mt-4 p-4 bg-zinc-800 rounded-lg border border-zinc-700">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3">
              <div>
                <div className="text-xs uppercase text-zinc-500">Regime</div>
                <div className="text-lg font-bold text-white uppercase">{regimeAdvice.regime}</div>
              </div>
              <div>
                <div className="text-xs uppercase text-zinc-500">Risk Multiplier</div>
                <div className="text-lg font-bold text-cyan-400">
                  {regimeAdvice.risk_multiplier.toFixed(2)}x
                </div>
              </div>
              <div>
                <div className="text-xs uppercase text-zinc-500">Entry Δ</div>
                <div className="text-lg font-bold text-blue-400">
                  {regimeAdvice.entry_delta > 0 ? "+" : ""}{(regimeAdvice.entry_delta * 100).toFixed(1)}%
                </div>
              </div>
              <div>
                <div className="text-xs uppercase text-zinc-500">Exit Δ</div>
                <div className="text-lg font-bold text-pink-400">
                  {regimeAdvice.exit_delta > 0 ? "+" : ""}{(regimeAdvice.exit_delta * 100).toFixed(1)}%
                </div>
              </div>
            </div>
            <div className="border-t border-zinc-700 pt-3">
              <div className="text-xs uppercase text-zinc-500 mb-1">Reasoning</div>
              <p className="text-zinc-300 text-sm">{regimeAdvice.reason}</p>
            </div>
          </div>
        )}
      </div>

      {/* Anomaly Explainer */}
      <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-6">
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          🔍 Anomaly Explainer
        </h2>
        <p className="text-gray-400 text-sm mb-4">
          Get AI explanations for system anomalies and actionable runbooks
        </p>
        
        <button
          onClick={explainAnomaly}
          disabled={anomalyLoading}
          className="px-6 py-2 bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-700 hover:to-orange-700 text-white font-semibold rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {anomalyLoading ? "Analyzing..." : "🚨 Explain Anomaly"}
        </button>

        {anomalyExplain && (
          <div className="mt-4 p-4 bg-zinc-800 rounded-lg border border-zinc-700">
            <div className="flex items-start gap-3 mb-3">
              <div className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${
                anomalyExplain.severity === "critical" ? "bg-red-600" :
                anomalyExplain.severity === "high" ? "bg-orange-600" :
                anomalyExplain.severity === "medium" ? "bg-yellow-600" :
                "bg-blue-600"
              }`}>
                {anomalyExplain.severity}
              </div>
            </div>
            
            <div className="mb-4">
              <div className="text-xs uppercase text-zinc-500 mb-1">Root Cause</div>
              <p className="text-zinc-300">{anomalyExplain.cause}</p>
            </div>

            <div>
              <div className="text-xs uppercase text-zinc-500 mb-2">Runbook</div>
              <ul className="space-y-2">
                {anomalyExplain.runbook.map((step, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm text-zinc-300">
                    <span className="text-cyan-400 font-bold">{idx + 1}.</span>
                    <span>{step}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}







