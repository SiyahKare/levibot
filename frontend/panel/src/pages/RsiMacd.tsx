/**
 * RSI + MACD Strategy Panel
 * ─────────────────────────────────────────
 * Combined RSI momentum + MACD trend strategy
 *
 * Modes:
 *   - Scalp: 1m TF, tight R (1.2x)
 *   - Day: 15m TF, moderate R (1.5-2x)
 *   - Swing: 4h TF, wide R (2-3x)
 */

import { useState } from "react";
import useSWR from "swr";
import { http } from "../lib/api";

interface RsiMacdHealth {
  running: boolean;
  mode: string;
  symbol: string;
  tf: string;
  position: string | null;
  features: {
    rsi: number;
    macd_line: number;
    macd_signal: number;
    macd_hist: number;
    atr: number;
    adx: number;
  };
  current_bar: number;
  cooldown_active: boolean;
  total_pnl: number;
  trades: number;
  win_rate: number;
}

interface RsiMacdParams {
  name: string;
  mode: string;
  symbol: string;
  tf: string;
  rsi: {
    period: number;
    enter_above: number;
    pullback_zone: [number, number];
  };
  macd: {
    fast: number;
    slow: number;
    signal: number;
  };
  risk: {
    atr_period: number;
    sl_atr_mult: number;
    tp_atr_mult: number;
    timeout_bars: number;
    fee_bps: number;
  };
  filters: {
    max_spread_bps: number;
    max_latency_ms: number;
    min_vol_bps_60s: number;
    min_adx?: number;
  };
  sizing: {
    quote_budget?: number;
    r_per_trade?: number;
    max_concurrent: number;
  };
  sync_bars: number;
  cooldown_bars: number;
  partial_take_profits?: number[];
}

interface Trade {
  timestamp: number;
  side: string;
  entry_price: number;
  exit_price: number;
  size: number;
  pnl: number;
  reason: string;
}

export default function RsiMacd() {
  const { data: health, mutate: refreshHealth } = useSWR<RsiMacdHealth>(
    "/strategy/rsi-macd/health",
    async (url) => {
      const res = await http(url);
      return res.json();
    },
    { refreshInterval: 2000 }
  );

  const { data: params, mutate: refreshParams } = useSWR<RsiMacdParams>(
    "/strategy/rsi-macd/params",
    async (url) => {
      const res = await http(url);
      return res.json();
    }
  );

  const { data: tradesData } = useSWR<{ trades: Trade[] }>(
    "/strategy/rsi-macd/trades/recent?limit=20",
    async (url) => {
      const res = await http(url);
      return res.json();
    },
    { refreshInterval: 5000 }
  );

  const [selectedMode, setSelectedMode] = useState<string>("day");
  const [isUpdating, setIsUpdating] = useState(false);

  const handleStart = async () => {
    setIsUpdating(true);
    try {
      await http("/strategy/rsi-macd/run?action=start", { method: "POST" });
      setTimeout(() => refreshHealth(), 500);
    } catch (err) {
      console.error("Start failed:", err);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleStop = async () => {
    setIsUpdating(true);
    try {
      await http("/strategy/rsi-macd/run?action=stop", { method: "POST" });
      setTimeout(() => refreshHealth(), 500);
    } catch (err) {
      console.error("Stop failed:", err);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleLoadPreset = async (mode: string) => {
    setIsUpdating(true);
    try {
      await http(`/strategy/rsi-macd/load-preset?mode=${mode}`, {
        method: "POST",
      });
      setSelectedMode(mode);
      setTimeout(() => {
        refreshParams();
        refreshHealth();
      }, 500);
    } catch (err) {
      console.error("Load preset failed:", err);
    } finally {
      setIsUpdating(false);
    }
  };

  const isRunning = health?.running ?? false;
  const features = health?.features;
  const trades = tradesData?.trades ?? [];

  return (
    <div style={{ padding: "2rem", maxWidth: "1200px", margin: "0 auto" }}>
      <div
        style={{
          background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
          color: "white",
          padding: "2rem",
          borderRadius: "12px",
          marginBottom: "2rem",
        }}
      >
        <h1 style={{ margin: 0, fontSize: "2rem", fontWeight: 700 }}>
          RSI + MACD Strategy
        </h1>
        <p style={{ margin: "0.5rem 0 0 0", opacity: 0.9 }}>
          Combined momentum + trend strategy •{" "}
          {health?.mode?.toUpperCase() || "DAY"} mode •{" "}
          {health?.symbol || "BTCUSDT"}
        </p>
      </div>

      {/* Status Card */}
      <div
        style={{
          background: "white",
          borderRadius: "12px",
          padding: "1.5rem",
          boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
          marginBottom: "1.5rem",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "1rem",
          }}
        >
          <h2 style={{ margin: 0, fontSize: "1.25rem" }}>Status</h2>
          <div
            style={{
              padding: "0.5rem 1rem",
              borderRadius: "20px",
              fontSize: "0.875rem",
              fontWeight: 600,
              background: isRunning ? "#10b981" : "#6b7280",
              color: "white",
            }}
          >
            {isRunning ? "RUNNING" : "STOPPED"}
          </div>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: "1rem",
          }}
        >
          <div>
            <div style={{ fontSize: "0.875rem", color: "#6b7280" }}>
              Position
            </div>
            <div style={{ fontSize: "1.25rem", fontWeight: 600 }}>
              {health?.position?.toUpperCase() || "FLAT"}
            </div>
          </div>
          <div>
            <div style={{ fontSize: "0.875rem", color: "#6b7280" }}>
              Total PnL
            </div>
            <div
              style={{
                fontSize: "1.25rem",
                fontWeight: 600,
                color: (health?.total_pnl ?? 0) >= 0 ? "#10b981" : "#ef4444",
              }}
            >
              ${health?.total_pnl?.toFixed(2) ?? "0.00"}
            </div>
          </div>
          <div>
            <div style={{ fontSize: "0.875rem", color: "#6b7280" }}>Trades</div>
            <div style={{ fontSize: "1.25rem", fontWeight: 600 }}>
              {health?.trades ?? 0}
            </div>
          </div>
          <div>
            <div style={{ fontSize: "0.875rem", color: "#6b7280" }}>
              Win Rate
            </div>
            <div style={{ fontSize: "1.25rem", fontWeight: 600 }}>
              {health?.win_rate?.toFixed(1) ?? "0.0"}%
            </div>
          </div>
        </div>
      </div>

      {/* Mode Selection & Controls */}
      <div
        style={{
          background: "white",
          borderRadius: "12px",
          padding: "1.5rem",
          boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
          marginBottom: "1.5rem",
        }}
      >
        <h2 style={{ margin: "0 0 1rem 0", fontSize: "1.25rem" }}>
          Mode & Controls
        </h2>

        <div style={{ marginBottom: "1.5rem" }}>
          <div
            style={{
              fontSize: "0.875rem",
              color: "#6b7280",
              marginBottom: "0.5rem",
            }}
          >
            Select Mode
          </div>
          <div style={{ display: "flex", gap: "0.75rem" }}>
            {["scalp", "day", "swing"].map((mode) => (
              <button
                key={mode}
                onClick={() => handleLoadPreset(mode)}
                disabled={isUpdating || isRunning}
                style={{
                  flex: 1,
                  padding: "0.75rem 1rem",
                  border:
                    selectedMode === mode
                      ? "2px solid #667eea"
                      : "2px solid #e5e7eb",
                  borderRadius: "8px",
                  background: selectedMode === mode ? "#f3f4f6" : "white",
                  color: selectedMode === mode ? "#667eea" : "#374151",
                  fontWeight: 600,
                  cursor: isRunning ? "not-allowed" : "pointer",
                  opacity: isUpdating || isRunning ? 0.5 : 1,
                  transition: "all 0.2s",
                }}
              >
                {mode.toUpperCase()}
              </button>
            ))}
          </div>
          {isRunning && (
            <div
              style={{
                fontSize: "0.75rem",
                color: "#ef4444",
                marginTop: "0.5rem",
              }}
            >
              ⚠️ Stop strategy before changing mode
            </div>
          )}
        </div>

        <div style={{ display: "flex", gap: "1rem" }}>
          <button
            onClick={handleStart}
            disabled={isRunning || isUpdating}
            style={{
              flex: 1,
              padding: "0.75rem 1.5rem",
              border: "none",
              borderRadius: "8px",
              background: isRunning ? "#9ca3af" : "#10b981",
              color: "white",
              fontWeight: 600,
              fontSize: "1rem",
              cursor: isRunning || isUpdating ? "not-allowed" : "pointer",
              transition: "all 0.2s",
            }}
          >
            {isUpdating ? "⏳" : "▶"} Start
          </button>
          <button
            onClick={handleStop}
            disabled={!isRunning || isUpdating}
            style={{
              flex: 1,
              padding: "0.75rem 1.5rem",
              border: "none",
              borderRadius: "8px",
              background: !isRunning ? "#9ca3af" : "#ef4444",
              color: "white",
              fontWeight: 600,
              fontSize: "1rem",
              cursor: !isRunning || isUpdating ? "not-allowed" : "pointer",
              transition: "all 0.2s",
            }}
          >
            {isUpdating ? "⏳" : "⏸"} Stop
          </button>
        </div>
      </div>

      {/* Features Card */}
      {features && (
        <div
          style={{
            background: "white",
            borderRadius: "12px",
            padding: "1.5rem",
            boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
            marginBottom: "1.5rem",
          }}
        >
          <h2 style={{ margin: "0 0 1rem 0", fontSize: "1.25rem" }}>
            Live Features
          </h2>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
              gap: "1rem",
            }}
          >
            <div>
              <div style={{ fontSize: "0.875rem", color: "#6b7280" }}>RSI</div>
              <div
                style={{
                  fontSize: "1.5rem",
                  fontWeight: 700,
                  color:
                    features.rsi > 70
                      ? "#ef4444"
                      : features.rsi < 30
                      ? "#10b981"
                      : "#374151",
                }}
              >
                {features.rsi.toFixed(1)}
              </div>
            </div>
            <div>
              <div style={{ fontSize: "0.875rem", color: "#6b7280" }}>
                MACD Hist
              </div>
              <div
                style={{
                  fontSize: "1.5rem",
                  fontWeight: 700,
                  color: features.macd_hist > 0 ? "#10b981" : "#ef4444",
                }}
              >
                {features.macd_hist.toFixed(2)}
              </div>
            </div>
            <div>
              <div style={{ fontSize: "0.875rem", color: "#6b7280" }}>
                MACD Line
              </div>
              <div style={{ fontSize: "1.125rem", fontWeight: 600 }}>
                {features.macd_line.toFixed(2)}
              </div>
            </div>
            <div>
              <div style={{ fontSize: "0.875rem", color: "#6b7280" }}>
                MACD Signal
              </div>
              <div style={{ fontSize: "1.125rem", fontWeight: 600 }}>
                {features.macd_signal.toFixed(2)}
              </div>
            </div>
            <div>
              <div style={{ fontSize: "0.875rem", color: "#6b7280" }}>ATR</div>
              <div style={{ fontSize: "1.125rem", fontWeight: 600 }}>
                {features.atr.toFixed(2)}
              </div>
            </div>
            <div>
              <div style={{ fontSize: "0.875rem", color: "#6b7280" }}>ADX</div>
              <div style={{ fontSize: "1.125rem", fontWeight: 600 }}>
                {features.adx.toFixed(1)}
              </div>
            </div>
          </div>

          {health?.cooldown_active && (
            <div
              style={{
                marginTop: "1rem",
                padding: "0.75rem",
                background: "#fef3c7",
                border: "1px solid #fbbf24",
                borderRadius: "8px",
                fontSize: "0.875rem",
                color: "#92400e",
              }}
            >
              ⏸ Cooldown active • Waiting for next entry window
            </div>
          )}
        </div>
      )}

      {/* Recent Trades */}
      <div
        style={{
          background: "white",
          borderRadius: "12px",
          padding: "1.5rem",
          boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
        }}
      >
        <h2 style={{ margin: "0 0 1rem 0", fontSize: "1.25rem" }}>
          Recent Trades
        </h2>

        {trades.length === 0 ? (
          <div
            style={{
              textAlign: "center",
              padding: "2rem",
              color: "#6b7280",
            }}
          >
            No trades yet
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                fontSize: "0.875rem",
              }}
            >
              <thead>
                <tr style={{ borderBottom: "2px solid #e5e7eb" }}>
                  <th style={{ padding: "0.75rem", textAlign: "left" }}>
                    Time
                  </th>
                  <th style={{ padding: "0.75rem", textAlign: "left" }}>
                    Side
                  </th>
                  <th style={{ padding: "0.75rem", textAlign: "right" }}>
                    Entry
                  </th>
                  <th style={{ padding: "0.75rem", textAlign: "right" }}>
                    Exit
                  </th>
                  <th style={{ padding: "0.75rem", textAlign: "right" }}>
                    PnL
                  </th>
                  <th style={{ padding: "0.75rem", textAlign: "left" }}>
                    Reason
                  </th>
                </tr>
              </thead>
              <tbody>
                {trades.map((trade, idx) => (
                  <tr key={idx} style={{ borderBottom: "1px solid #f3f4f6" }}>
                    <td style={{ padding: "0.75rem" }}>
                      {new Date(trade.timestamp * 1000).toLocaleTimeString()}
                    </td>
                    <td
                      style={{
                        padding: "0.75rem",
                        fontWeight: 600,
                        color: trade.side === "long" ? "#10b981" : "#ef4444",
                      }}
                    >
                      {trade.side.toUpperCase()}
                    </td>
                    <td style={{ padding: "0.75rem", textAlign: "right" }}>
                      ${trade.entry_price.toFixed(2)}
                    </td>
                    <td style={{ padding: "0.75rem", textAlign: "right" }}>
                      ${trade.exit_price.toFixed(2)}
                    </td>
                    <td
                      style={{
                        padding: "0.75rem",
                        textAlign: "right",
                        fontWeight: 600,
                        color: trade.pnl >= 0 ? "#10b981" : "#ef4444",
                      }}
                    >
                      ${trade.pnl.toFixed(2)}
                    </td>
                    <td
                      style={{
                        padding: "0.75rem",
                        fontSize: "0.75rem",
                        color: "#6b7280",
                      }}
                    >
                      {trade.reason}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

