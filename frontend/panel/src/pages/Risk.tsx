/**
 * Risk Page
 * Apply risk presets and view current risk parameters
 */
import { api } from "@/lib/api";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import useSWR from "swr";

const PRESETS = ["safe", "normal", "aggressive"] as const;
const AVAILABLE_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"];

export default function Risk() {
  const { data: current, mutate: mutateCurrent } = useSWR(
    "/risk/current",
    api.riskCurrent,
    { refreshInterval: 15_000 }
  );

  const { data: presets } = useSWR("/risk/presets", api.riskPresets);
  const { data: guardrailsData, mutate: mutateGuardrails } = useSWR(
    "/risk/guardrails",
    api.guardrails,
    { refreshInterval: 10_000 }
  );

  const [busy, setBusy] = useState<string | null>(null);
  const [activePreset, setActivePreset] = useState<string>("normal");

  // Guardrails local state
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.55);
  const [maxTradeUsd, setMaxTradeUsd] = useState(500);
  const [maxDailyLoss, setMaxDailyLoss] = useState(-200);
  const [cooldownMinutes, setCooldownMinutes] = useState(30);
  const [circuitBreakerMs, setCircuitBreakerMs] = useState(300);
  const [circuitBreakerEnabled, setCircuitBreakerEnabled] = useState(true);
  const [symbolAllowlist, setSymbolAllowlist] = useState<string[]>([
    "BTCUSDT",
    "ETHUSDT",
  ]);
  const [guardrailsBusy, setGuardrailsBusy] = useState(false);

  // Sync with backend data
  useEffect(() => {
    if (guardrailsData?.guardrails) {
      const g = guardrailsData.guardrails;
      setConfidenceThreshold(g.confidence_threshold);
      setMaxTradeUsd(g.max_trade_usd);
      setMaxDailyLoss(g.max_daily_loss);
      setCooldownMinutes(g.cooldown_minutes);
      setCircuitBreakerMs(g.circuit_breaker_latency_ms);
      setCircuitBreakerEnabled(g.circuit_breaker_enabled);
      setSymbolAllowlist(g.symbol_allowlist || []);
    }
  }, [guardrailsData]);

  const applyPreset = async (name: (typeof PRESETS)[number]) => {
    setBusy(name);
    try {
      await api.setRiskPreset(name);
      setActivePreset(name);
      mutateCurrent();
      toast.success(`Preset applied: ${name.toUpperCase()}`);
    } catch (error: any) {
      console.error("Failed to set preset:", error);
      toast.error(`Preset failed: ${error.message || "Unknown error"}`);
    } finally {
      setBusy(null);
    }
  };

  const saveGuardrails = async () => {
    setGuardrailsBusy(true);
    try {
      await api.updateGuardrails({
        confidence_threshold: confidenceThreshold,
        max_trade_usd: maxTradeUsd,
        max_daily_loss: maxDailyLoss,
        cooldown_minutes: cooldownMinutes,
        circuit_breaker_latency_ms: circuitBreakerMs,
        circuit_breaker_enabled: circuitBreakerEnabled,
        symbol_allowlist: symbolAllowlist,
      });
      mutateGuardrails();
      toast.success("✅ Guardrails updated successfully");
    } catch (error: any) {
      console.error("Failed to update guardrails:", error);
      toast.error(`Failed: ${error.message || "Unknown error"}`);
    } finally {
      setGuardrailsBusy(false);
    }
  };

  const handleTriggerCooldown = async () => {
    try {
      await api.triggerCooldown();
      mutateGuardrails();
      toast.success("🧊 Cooldown triggered");
    } catch (error: any) {
      toast.error(`Failed: ${error.message || "Unknown error"}`);
    }
  };

  const handleClearCooldown = async () => {
    try {
      await api.clearCooldown();
      mutateGuardrails();
      toast.success("✅ Cooldown cleared");
    } catch (error: any) {
      toast.error(`Failed: ${error.message || "Unknown error"}`);
    }
  };

  const toggleSymbol = (symbol: string) => {
    if (symbolAllowlist.includes(symbol)) {
      setSymbolAllowlist(symbolAllowlist.filter((s) => s !== symbol));
    } else {
      setSymbolAllowlist([...symbolAllowlist, symbol]);
    }
  };

  const currentParams = current?.parameters || {};
  const cooldownActive = guardrailsData?.state?.cooldown_active || false;
  const cooldownRemaining = guardrailsData?.state?.cooldown_remaining_sec || 0;

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-zinc-900">Risk Management</h1>
        <p className="text-zinc-600 mt-2">
          Apply risk presets or view current parameters
        </p>
      </div>

      {/* Preset Buttons */}
      <div className="p-6 rounded-2xl shadow bg-white border border-zinc-200">
        <h2 className="text-lg font-semibold text-zinc-900 mb-4">
          Risk Presets
        </h2>
        <div className="flex flex-wrap gap-3">
          {PRESETS.map((preset) => (
            <button
              key={preset}
              onClick={() => applyPreset(preset)}
              disabled={busy !== null}
              className={`px-6 py-3 rounded-xl font-medium transition-all ${
                activePreset === preset
                  ? "bg-zinc-900 text-white shadow-lg"
                  : "bg-zinc-100 text-zinc-700 hover:bg-zinc-200"
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {busy === preset ? "Applying..." : preset.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Current Parameters */}
      <div className="p-6 rounded-2xl shadow bg-white border border-zinc-200">
        <h2 className="text-lg font-semibold text-zinc-900 mb-4">
          Current Parameters
          <span className="ml-3 text-sm font-normal text-zinc-500">
            (Preset: {current?.preset || "unknown"})
          </span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-lg bg-zinc-50">
            <div className="text-sm text-zinc-600 mb-1">Max Daily Loss</div>
            <div className="text-2xl font-bold text-rose-600">
              ${currentParams.MAX_DAILY_LOSS || 0}
            </div>
          </div>
          <div className="p-4 rounded-lg bg-zinc-50">
            <div className="text-sm text-zinc-600 mb-1">
              Max Position Notional
            </div>
            <div className="text-2xl font-bold text-zinc-900">
              ${currentParams.MAX_POS_NOTIONAL || 0}
            </div>
          </div>
          <div className="p-4 rounded-lg bg-zinc-50">
            <div className="text-sm text-zinc-600 mb-1">Slippage (BPS)</div>
            <div className="text-2xl font-bold text-zinc-900">
              {currentParams.SLIPPAGE_BPS || 0}
            </div>
          </div>
          <div className="p-4 rounded-lg bg-zinc-50">
            <div className="text-sm text-zinc-600 mb-1">Fee Taker (BPS)</div>
            <div className="text-2xl font-bold text-zinc-900">
              {currentParams.FEE_TAKER_BPS || 0}
            </div>
          </div>
        </div>
      </div>

      {/* Trade Guardrails */}
      <div className="p-6 rounded-2xl shadow bg-white border border-zinc-200">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-zinc-900 flex items-center gap-2">
              🛡️ Trade Guardrails
            </h2>
            <p className="text-sm text-zinc-600 mt-1">
              Safety limits and circuit breakers for AI trading
            </p>
          </div>
          {cooldownActive && (
            <div className="px-4 py-2 rounded-lg bg-blue-50 border border-blue-200">
              <span className="text-sm font-semibold text-blue-900">
                🧊 Cooldown: {Math.floor(cooldownRemaining / 60)}m{" "}
                {cooldownRemaining % 60}s
              </span>
            </div>
          )}
        </div>

        <div className="space-y-6">
          {/* Confidence Threshold */}
          <div>
            <div className="flex justify-between mb-2">
              <label className="text-sm font-medium text-zinc-700">
                Confidence Threshold
              </label>
              <span className="text-sm font-mono font-semibold text-blue-600">
                {confidenceThreshold.toFixed(2)}
              </span>
            </div>
            <input
              type="range"
              min="0.5"
              max="1.0"
              step="0.01"
              value={confidenceThreshold}
              onChange={(e) =>
                setConfidenceThreshold(parseFloat(e.target.value))
              }
              className="w-full h-2 bg-zinc-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
            <p className="text-xs text-zinc-500 mt-1">
              Minimum prob_up to execute trades
            </p>
          </div>

          {/* Max Trade USD */}
          <div>
            <div className="flex justify-between mb-2">
              <label className="text-sm font-medium text-zinc-700">
                Max Trade Size (USD)
              </label>
              <span className="text-sm font-mono font-semibold text-blue-600">
                ${maxTradeUsd}
              </span>
            </div>
            <input
              type="range"
              min="100"
              max="2000"
              step="50"
              value={maxTradeUsd}
              onChange={(e) => setMaxTradeUsd(parseInt(e.target.value))}
              className="w-full h-2 bg-zinc-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
            <p className="text-xs text-zinc-500 mt-1">
              Maximum notional per single trade
            </p>
          </div>

          {/* Max Daily Loss */}
          <div>
            <div className="flex justify-between mb-2">
              <label className="text-sm font-medium text-zinc-700">
                Max Daily Loss (USD)
              </label>
              <span className="text-sm font-mono font-semibold text-rose-600">
                ${maxDailyLoss}
              </span>
            </div>
            <input
              type="range"
              min="-500"
              max="0"
              step="10"
              value={maxDailyLoss}
              onChange={(e) => setMaxDailyLoss(parseInt(e.target.value))}
              className="w-full h-2 bg-zinc-200 rounded-lg appearance-none cursor-pointer accent-rose-600"
            />
            <p className="text-xs text-zinc-500 mt-1">
              Auto-stop trading if loss exceeds this
            </p>
          </div>

          {/* Cooldown Minutes */}
          <div>
            <div className="flex justify-between mb-2">
              <label className="text-sm font-medium text-zinc-700">
                Cooldown Period (minutes)
              </label>
              <span className="text-sm font-mono font-semibold text-blue-600">
                {cooldownMinutes}m
              </span>
            </div>
            <input
              type="range"
              min="5"
              max="120"
              step="5"
              value={cooldownMinutes}
              onChange={(e) => setCooldownMinutes(parseInt(e.target.value))}
              className="w-full h-2 bg-zinc-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
            <p className="text-xs text-zinc-500 mt-1">
              Pause duration after daily loss limit hit
            </p>
          </div>

          {/* Circuit Breaker */}
          <div className="flex items-center justify-between p-4 rounded-lg bg-zinc-50">
            <div>
              <div className="text-sm font-medium text-zinc-700">
                Circuit Breaker
              </div>
              <div className="text-xs text-zinc-500 mt-1">
                Auto-fallback if p95 latency {">"} {circuitBreakerMs}ms
              </div>
            </div>
            <button
              onClick={() => setCircuitBreakerEnabled(!circuitBreakerEnabled)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                circuitBreakerEnabled ? "bg-blue-600" : "bg-zinc-300"
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  circuitBreakerEnabled ? "translate-x-6" : "translate-x-1"
                }`}
              />
            </button>
          </div>

          {/* Circuit Breaker Latency Threshold */}
          {circuitBreakerEnabled && (
            <div>
              <div className="flex justify-between mb-2">
                <label className="text-sm font-medium text-zinc-700">
                  Latency Threshold (ms)
                </label>
                <span className="text-sm font-mono font-semibold text-amber-600">
                  {circuitBreakerMs}ms
                </span>
              </div>
              <input
                type="range"
                min="100"
                max="1000"
                step="50"
                value={circuitBreakerMs}
                onChange={(e) => setCircuitBreakerMs(parseInt(e.target.value))}
                className="w-full h-2 bg-zinc-200 rounded-lg appearance-none cursor-pointer accent-amber-600"
              />
            </div>
          )}

          {/* Symbol Allowlist */}
          <div>
            <div className="text-sm font-medium text-zinc-700 mb-3">
              Symbol Allowlist
            </div>
            <div className="flex flex-wrap gap-2">
              {AVAILABLE_SYMBOLS.map((symbol) => (
                <button
                  key={symbol}
                  onClick={() => toggleSymbol(symbol)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    symbolAllowlist.includes(symbol)
                      ? "bg-blue-600 text-white shadow-md"
                      : "bg-zinc-100 text-zinc-600 hover:bg-zinc-200"
                  }`}
                >
                  {symbol}
                </button>
              ))}
            </div>
            <p className="text-xs text-zinc-500 mt-2">
              Only selected symbols can be traded
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4 border-t border-zinc-200">
            <button
              onClick={saveGuardrails}
              disabled={guardrailsBusy}
              className="flex-1 px-6 py-3 rounded-xl font-semibold text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg"
            >
              {guardrailsBusy ? "Saving..." : "💾 Save Guardrails"}
            </button>

            {cooldownActive ? (
              <button
                onClick={handleClearCooldown}
                className="px-6 py-3 rounded-xl font-semibold text-white bg-green-600 hover:bg-green-700 transition-all shadow-md hover:shadow-lg"
              >
                ✅ Clear Cooldown
              </button>
            ) : (
              <button
                onClick={handleTriggerCooldown}
                className="px-6 py-3 rounded-xl font-semibold text-white bg-amber-600 hover:bg-amber-700 transition-all shadow-md hover:shadow-lg"
              >
                🧊 Trigger Cooldown
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Preset Details */}
      {presets && (
        <div className="p-6 rounded-2xl shadow bg-zinc-50 border border-zinc-200">
          <h2 className="text-lg font-semibold text-zinc-900 mb-4">
            Preset Details
          </h2>
          <div className="space-y-4">
            {Object.entries(presets.presets || {}).map(
              ([name, params]: [string, any]) => (
                <details key={name} className="group">
                  <summary className="cursor-pointer font-medium text-zinc-900 hover:text-zinc-700">
                    {name.toUpperCase()}
                  </summary>
                  <pre className="mt-2 p-3 rounded bg-white text-xs overflow-auto">
                    {JSON.stringify(params, null, 2)}
                  </pre>
                </details>
              )
            )}
          </div>
        </div>
      )}
    </div>
  );
}
