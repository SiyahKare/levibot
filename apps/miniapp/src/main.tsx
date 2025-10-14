/**
 * LeviBot Mini App - Telegram WebApp Control Panel
 * Enterprise trading control center
 */
import { initMiniApp, initViewport } from "@telegram-apps/sdk";
import React, { useEffect, useState } from "react";
import ReactDOM from "react-dom/client";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import useSWR from "swr";
import "./index.css";

// API Configuration
const API_BASE = import.meta.env.VITE_API_BASE || "https://api.levibot.app";

const fetcher = (url: string) =>
  fetch(`${API_BASE}${url}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
  }).then((r) => r.json());

// Types
interface SystemStatus {
  equity: number;
  daily_pnl: number;
  daily_dd_pct: number;
  exposure_pct: number;
  num_positions: number;
  daily_trades: number;
  kill_switch: boolean;
  positions: Record<string, number>;
  limits: {
    max_daily_trades: number;
    max_daily_loss: number;
    max_daily_dd_pct: number;
    max_exposure_pct: number;
  };
}

interface EquityPoint {
  ts: string;
  equity: number;
  realized_pnl: number;
  unrealized_pnl: number;
}

interface Signal {
  symbol: string;
  strategy: string;
  side: number;
  confidence: number;
  reason: string;
  ts: string;
}

// Main App Component
function App() {
  const [miniApp] = useState(() => {
    try {
      return initMiniApp();
    } catch {
      return null;
    }
  });

  const [viewport] = useState(() => {
    try {
      return initViewport();
    } catch {
      return null;
    }
  });

  useEffect(() => {
    if (miniApp) {
      miniApp.ready();
      miniApp.setHeaderColor("#1a1a1a");
    }
    if (viewport) {
      viewport.expand();
    }
  }, [miniApp, viewport]);

  // Fetch data
  const { data: status, mutate: refetchStatus } = useSWR<SystemStatus>(
    "/policy/status",
    fetcher,
    { refreshInterval: 5000 }
  );

  const { data: equityCurve } = useSWR<EquityPoint[]>(
    "/analytics/equity?hours=24",
    fetcher,
    { refreshInterval: 30000 }
  );

  const { data: recentSignals } = useSWR<Signal[]>(
    "/signals/recent?limit=10",
    fetcher,
    { refreshInterval: 10000 }
  );

  // Actions
  const toggleKillSwitch = async () => {
    try {
      const action = status?.kill_switch ? "deactivate" : "activate";
      await fetch(`${API_BASE}/policy/killswitch/${action}`, {
        method: "POST",
        credentials: "include",
      });
      refetchStatus();

      if (miniApp) {
        miniApp.showAlert(
          status?.kill_switch
            ? "Kill switch deactivated"
            : "Kill switch activated"
        );
      }
    } catch (err) {
      console.error("Failed to toggle kill switch:", err);
      if (miniApp) {
        miniApp.showAlert("Error toggling kill switch");
      }
    }
  };

  const resetDailyStats = async () => {
    try {
      await fetch(`${API_BASE}/policy/reset_daily`, {
        method: "POST",
        credentials: "include",
      });
      refetchStatus();

      if (miniApp) {
        miniApp.showAlert("Daily stats reset");
      }
    } catch (err) {
      console.error("Failed to reset stats:", err);
    }
  };

  if (!status) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <h1>🤖 LeviBot</h1>
        <div className="status-badge">
          {status.kill_switch ? (
            <span className="badge danger">🚨 KILL SWITCH</span>
          ) : (
            <span className="badge success">✅ Active</span>
          )}
        </div>
      </header>

      {/* Equity Card */}
      <div className="card">
        <h2>💰 Portfolio</h2>
        <div className="metric-grid">
          <div className="metric">
            <span className="label">Equity</span>
            <span className="value">${status.equity.toLocaleString()}</span>
          </div>
          <div className="metric">
            <span className="label">24h PnL</span>
            <span
              className={`value ${
                status.daily_pnl >= 0 ? "positive" : "negative"
              }`}
            >
              ${status.daily_pnl >= 0 ? "+" : ""}
              {status.daily_pnl.toFixed(2)}
            </span>
          </div>
          <div className="metric">
            <span className="label">Drawdown</span>
            <span className="value">
              {(status.daily_dd_pct * 100).toFixed(2)}%
            </span>
          </div>
          <div className="metric">
            <span className="label">Exposure</span>
            <span className="value">
              {(status.exposure_pct * 100).toFixed(1)}%
            </span>
          </div>
        </div>

        {/* Equity Chart */}
        {equityCurve && equityCurve.length > 0 && (
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={equityCurve}>
                <defs>
                  <linearGradient id="colorEquity" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis
                  dataKey="ts"
                  stroke="#666"
                  tick={{ fontSize: 10 }}
                  tickFormatter={(ts) =>
                    new Date(ts).toLocaleTimeString("en-US", {
                      hour: "2-digit",
                      minute: "2-digit",
                    })
                  }
                />
                <YAxis stroke="#666" tick={{ fontSize: 10 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1a1a1a",
                    border: "1px solid #333",
                  }}
                  formatter={(value: number) => `$${value.toFixed(2)}`}
                />
                <Area
                  type="monotone"
                  dataKey="equity"
                  stroke="#3b82f6"
                  fillOpacity={1}
                  fill="url(#colorEquity)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Trading Stats */}
      <div className="card">
        <h2>📊 Trading Activity</h2>
        <div className="stat-row">
          <span>Daily Trades</span>
          <span>
            {status.daily_trades} / {status.limits.max_daily_trades}
          </span>
        </div>
        <div className="stat-row">
          <span>Open Positions</span>
          <span>{status.num_positions}</span>
        </div>
        <div className="stat-row">
          <span>Max Daily Loss</span>
          <span>${status.limits.max_daily_loss}</span>
        </div>
        <div className="stat-row">
          <span>Max DD Limit</span>
          <span>{(status.limits.max_daily_dd_pct * 100).toFixed(1)}%</span>
        </div>
      </div>

      {/* Positions */}
      {status.num_positions > 0 && (
        <div className="card">
          <h2>📍 Open Positions</h2>
          <div className="positions-list">
            {Object.entries(status.positions).map(([symbol, size]) => (
              <div key={symbol} className="position-item">
                <span className="symbol">{symbol}</span>
                <span className="size">${size.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Signals */}
      {recentSignals && recentSignals.length > 0 && (
        <div className="card">
          <h2>🎯 Recent Signals</h2>
          <div className="signals-list">
            {recentSignals.map((signal, idx) => (
              <div key={idx} className="signal-item">
                <div className="signal-header">
                  <span className="signal-symbol">
                    {signal.side > 0 ? "🟢" : signal.side < 0 ? "🔴" : "⚪"}{" "}
                    {signal.symbol}
                  </span>
                  <span className="signal-confidence">
                    {(signal.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="signal-meta">
                  <span className="signal-strategy">{signal.strategy}</span>
                  <span className="signal-reason">{signal.reason}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Controls */}
      <div className="card">
        <h2>🎛️ Controls</h2>
        <div className="button-grid">
          <button
            className={`btn ${
              status.kill_switch ? "btn-success" : "btn-danger"
            }`}
            onClick={toggleKillSwitch}
          >
            {status.kill_switch ? "✅ Resume Trading" : "🚨 Kill Switch"}
          </button>
          <button className="btn btn-secondary" onClick={resetDailyStats}>
            🔄 Reset Daily Stats
          </button>
        </div>
      </div>

      {/* Footer */}
      <footer className="footer">
        <p>LeviBot v1.0.0 • Enterprise AI Trading</p>
      </footer>
    </div>
  );
}

// Mount app
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
