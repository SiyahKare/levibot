import { useState } from "react";
import useSWR from "swr";
import AIExplainerModal from "../components/ai/AIExplainerModal";
import AIImpactTicker from "../components/ai/AIImpactTicker";
import AIRegimeCard from "../components/ai/AIRegimeCard";
import ControlBar from "../components/ml/ControlBar";
import KpiCard from "../components/ml/KpiCard";
import SignalCard from "../components/ml/SignalCard";
import StatusBanner from "../components/ml/StatusBanner";
import {
  getAutomationStatus,
  getHealth,
  getMetricsText,
  getPredict,
  getPredictDeep,
  postAutomationStart,
  postKill,
} from "../lib/mlApi";
import { getGauge, parsePrometheusText } from "../lib/prometheus";

type TabType = "overview" | "signals" | "risk" | "ai" | "logs";

const SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"];

export default function MLDashboard() {
  const [activeTab, setActiveTab] = useState<TabType>("overview");
  const [explainerOpen, setExplainerOpen] = useState(false);
  const [explainerContext, setExplainerContext] = useState<any>(null);
  const [newsImpacts, setNewsImpacts] = useState<any[]>([]);

  // Health & Metrics polling
  const { data: health } = useSWR("health", getHealth, {
    refreshInterval: 5000,
  });
  const { data: metricsText } = useSWR("metrics", getMetricsText, {
    refreshInterval: 15000,
    shouldRetryOnError: false,
  });
  const { data: autoStatus, mutate: mutateAutoStatus } = useSWR(
    "automation-status",
    getAutomationStatus,
    { refreshInterval: 5000 }
  );

  // Parse Prometheus metrics
  const metrics = metricsText ? parsePrometheusText(metricsText) : [];
  const staleness = getGauge(metrics, "ml_feature_staleness_seconds");
  const ece = getGauge(metrics, "model_calibration_ece");
  const pnl1d = getGauge(metrics, "levibot_paper_pnl", { window: "1d" });
  const pnl7d = getGauge(metrics, "levibot_paper_pnl", { window: "7d" });

  // KPI status calculation
  const stalenessStatus =
    staleness === null
      ? "gray"
      : staleness <= 900
      ? "green"
      : staleness <= 1800
      ? "amber"
      : "red";
  const eceStatus =
    ece === null
      ? "gray"
      : ece <= 0.05
      ? "green"
      : ece <= 0.06
      ? "amber"
      : "red";

  // Controls
  const handleKillSwitch = async (enabled: boolean) => {
    await postKill(enabled);
    mutateAutoStatus();
  };

  const handleCanaryChange = async (fraction: number) => {
    await postAutomationStart({ canary_fraction: fraction });
    mutateAutoStatus();
  };

  const handleStartMarathon = async () => {
    await postAutomationStart({ canary_fraction: 0.1 });
    mutateAutoStatus();
  };

  const handleEvaluate = () => {
    if (!health || !autoStatus) return;
    const criteria = {
      ece: ece && ece <= 0.06,
      staleness: staleness && staleness <= 1800,
      health: health.ok,
      trades: (autoStatus.trades_today ?? 0) >= 20,
    };
    const passed = Object.values(criteria).filter(Boolean).length;
    alert(
      `48h Evaluation:\n\n` +
        `ECE: ${ece?.toFixed(4) ?? "N/A"} ${criteria.ece ? "✅" : "❌"}\n` +
        `Staleness: ${staleness?.toFixed(0) ?? "N/A"}s ${
          criteria.staleness ? "✅" : "❌"
        }\n` +
        `Health: ${health.ok ? "OK" : "FAIL"} ${
          criteria.health ? "✅" : "❌"
        }\n` +
        `Trades: ${autoStatus.trades_today ?? 0} ${
          criteria.trades ? "✅" : "❌"
        }\n\n` +
        `Result: ${passed}/4 passed. ${
          passed >= 3 ? "✅ READY TO PROMOTE" : "❌ NEEDS IMPROVEMENT"
        }`
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">🧠 ML Dashboard</h1>
          <p className="text-gray-400 mt-1">
            Production-grade AI monitoring & control
          </p>
        </div>
        <div className="text-sm text-gray-500">
          {new Date().toLocaleTimeString()}
        </div>
      </div>

      {/* Status Banner */}
      {health && <StatusBanner health={health} ece={ece ?? undefined} />}

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KpiCard
          title="Feature Staleness"
          value={staleness !== null ? `${staleness.toFixed(0)}s` : "N/A"}
          subtitle={metricsText ? "Live from Prometheus" : "Metrics offline"}
          status={stalenessStatus}
        />
        <KpiCard
          title="Model ECE"
          value={ece !== null ? ece.toFixed(4) : "N/A"}
          subtitle="Calibration quality"
          status={eceStatus}
        />
        <KpiCard
          title="1D Paper PnL"
          value={pnl1d !== null ? `${(pnl1d * 100).toFixed(2)}%` : "N/A"}
          subtitle="24h performance"
          trend={
            pnl1d && pnl1d > 0 ? "up" : pnl1d && pnl1d < 0 ? "down" : "neutral"
          }
          status={pnl1d && pnl1d > 0 ? "green" : "gray"}
        />
        <KpiCard
          title="7D Paper PnL"
          value={pnl7d !== null ? `${(pnl7d * 100).toFixed(2)}%` : "N/A"}
          subtitle="Weekly performance"
          trend={
            pnl7d && pnl7d > 0 ? "up" : pnl7d && pnl7d < 0 ? "down" : "neutral"
          }
          status={pnl7d && pnl7d > 0 ? "green" : "gray"}
        />
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-zinc-800 pb-2">
        {(["overview", "signals", "risk", "ai", "logs"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-t-lg font-semibold transition-all ${
              activeTab === tab
                ? "bg-blue-600 text-white"
                : "bg-zinc-800 text-gray-400 hover:bg-zinc-700"
            }`}
          >
            {tab === "ai"
              ? "🧠 AI"
              : tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === "overview" && (
        <OverviewTab autoStatus={autoStatus} health={health} />
      )}
      {activeTab === "signals" && <SignalsTab symbols={SYMBOLS} />}
      {activeTab === "risk" && (
        <ControlBar
          killSwitchEnabled={autoStatus?.enabled === false}
          canaryFraction={autoStatus?.canary_fraction ?? 0}
          onKillSwitch={handleKillSwitch}
          onCanaryChange={handleCanaryChange}
          onStartMarathon={handleStartMarathon}
          onEvaluate={handleEvaluate}
        />
      )}
      {activeTab === "ai" && (
        <AITab
          metrics={{
            staleness,
            ece,
            pnl1d,
            pnl7d,
            volatility: 0.5,
            trend: 0.3,
          }}
          newsImpacts={newsImpacts}
          onExplain={(context) => {
            setExplainerContext(context);
            setExplainerOpen(true);
          }}
        />
      )}
      {activeTab === "logs" && <LogsTab />}

      {/* AI Explainer Modal */}
      <AIExplainerModal
        isOpen={explainerOpen}
        onClose={() => setExplainerOpen(false)}
        context={explainerContext}
      />
    </div>
  );
}

// ============ Tab Components ============

function OverviewTab({ autoStatus, health }: any) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="rounded-lg border border-zinc-700 bg-zinc-800/50 p-4">
          <h3 className="text-sm font-semibold text-gray-400 mb-2">
            Automation Status
          </h3>
          <p className="text-2xl font-bold text-white">
            {autoStatus?.enabled ? "✅ ACTIVE" : "🛑 PAUSED"}
          </p>
        </div>
        <div className="rounded-lg border border-zinc-700 bg-zinc-800/50 p-4">
          <h3 className="text-sm font-semibold text-gray-400 mb-2">
            Trades Today
          </h3>
          <p className="text-2xl font-bold text-white">
            {autoStatus?.trades_today ?? 0}
          </p>
        </div>
        <div className="rounded-lg border border-zinc-700 bg-zinc-800/50 p-4">
          <h3 className="text-sm font-semibold text-gray-400 mb-2">Regime</h3>
          <p className="text-2xl font-bold text-white">
            {autoStatus?.regime ?? "NEUTRAL"}
          </p>
        </div>
      </div>

      {autoStatus && (
        <div className="rounded-lg border border-zinc-700 bg-zinc-800/50 p-4">
          <h3 className="text-lg font-semibold text-white mb-3">
            Performance Metrics
          </h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-400">Sharpe Ratio</p>
              <p className="text-lg font-bold text-green-400">
                {autoStatus.sharpe?.toFixed(2) ?? "N/A"}
              </p>
            </div>
            <div>
              <p className="text-gray-400">Max Drawdown</p>
              <p className="text-lg font-bold text-red-400">
                {autoStatus.max_dd
                  ? `${(autoStatus.max_dd * 100).toFixed(1)}%`
                  : "N/A"}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function SignalsTab({ symbols }: { symbols: string[] }) {
  return (
    <div className="space-y-6">
      {symbols.map((symbol) => (
        <SymbolSignals key={symbol} symbol={symbol} />
      ))}
    </div>
  );
}

function SymbolSignals({ symbol }: { symbol: string }) {
  const { data: lgbm } = useSWR(`predict-${symbol}`, () => getPredict(symbol));
  const { data: deep } = useSWR(`predict-deep-${symbol}`, () =>
    getPredictDeep(symbol)
  );

  return (
    <div>
      <h3 className="text-xl font-bold text-white mb-3">{symbol}</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {lgbm && (
          <SignalCard
            symbol={symbol}
            modelTitle="📊 LightGBM"
            p_up={lgbm.p_up}
            confidence={lgbm.confidence}
            extra={{
              auc: lgbm.model_metrics.auc,
              brier: lgbm.model_metrics.brier,
            }}
          />
        )}
        {deep && (
          <SignalCard
            symbol={symbol}
            modelTitle="🧠 Deep Transformer"
            p_up={deep.p_up}
            confidence={deep.confidence}
            extra={{
              mu: deep.mu,
              uncertainty: deep.uncertainty,
            }}
          />
        )}
      </div>
    </div>
  );
}

function LogsTab() {
  return (
    <div className="rounded-lg border border-zinc-700 bg-zinc-800/50 p-6">
      <h3 className="text-xl font-bold text-white mb-4">
        📜 Shadow Predictions Log
      </h3>
      <div className="bg-yellow-900/20 border border-yellow-700 rounded-lg p-6 mb-4">
        <div className="flex items-start gap-3">
          <span className="text-3xl">⚠️</span>
          <div>
            <h4 className="text-lg font-semibold text-yellow-300 mb-2">
              Özellik Henüz Aktif Değil
            </h4>
            <p className="text-yellow-200 text-sm mb-3">
              Canlı log takibi özelliği şu anda geliştirme aşamasındadır. Bu
              özellik için backend'de log streaming endpoint'i eklenmesi
              gerekmektedir.
            </p>
            <div className="text-xs text-yellow-300 space-y-1">
              <p>
                <strong>Manuel erişim için:</strong>
              </p>
              <code className="block bg-black/30 p-2 rounded mt-1">
                tail -f backend/data/logs/shadow/predictions_*.jsonl
              </code>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-zinc-900 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-zinc-400 mb-2">
          Planlanan Özellikler:
        </h4>
        <ul className="text-sm text-zinc-400 space-y-1 list-disc list-inside">
          <li>Server-Sent Events (SSE) ile canlı log akışı</li>
          <li>Filtreleme ve arama özellikleri</li>
          <li>Log seviyesi seçimi (info, warning, error)</li>
          <li>Log export ve download özellikleri</li>
        </ul>
      </div>
    </div>
  );
}

function AITab({
  metrics,
  newsImpacts,
  onExplain,
}: {
  metrics: any;
  newsImpacts: any[];
  onExplain: (context: any) => void;
}) {
  return (
    <div className="space-y-6">
      {/* AI Regime Card */}
      <AIRegimeCard metrics={metrics} />

      {/* AI Impact Ticker */}
      <AIImpactTicker impacts={newsImpacts} />

      {/* Explainer Button */}
      <div className="rounded-xl border border-zinc-700 bg-zinc-800/50 p-6">
        <h3 className="text-xl font-bold text-white mb-4">
          🤖 Anomaly Explainer
        </h3>
        <p className="text-gray-400 text-sm mb-4">
          Use AI to analyze and explain system anomalies with actionable
          runbooks.
        </p>
        <button
          onClick={() =>
            onExplain({
              ece: metrics.ece,
              staleness: metrics.staleness,
              pnl1d: metrics.pnl1d,
              pnl7d: metrics.pnl7d,
            })
          }
          className="w-full px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold rounded-lg transition"
        >
          🧠 Explain Current State
        </button>
      </div>
    </div>
  );
}
