/**
 * Main App Component
 * Routing and navigation for LEVIBOT Panel
 */
import DarkModeToggle from "@/components/DarkModeToggle";
import { ReplayBadge } from "@/components/ReplayBadge";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";
import AIBrain from "@/pages/AIBrain";
import Alerts from "@/pages/Alerts";
import Analytics from "@/pages/Analytics";
import Daytrade from "@/pages/Daytrade";
import EventsTimeline from "@/pages/EventsTimeline";
import Integrations from "@/pages/Integrations";
import MEVFeed from "@/pages/MEVFeed";
import MLDashboard from "@/pages/MLDashboard";
import NFTSniper from "@/pages/NFTSniper";
import OnChain from "@/pages/OnChain";
import Ops from "@/pages/Ops";
import Overview from "@/pages/Overview";
import Paper from "@/pages/Paper";
import Risk from "@/pages/Risk";
import RsiMacd from "@/pages/RsiMacd";
import Scalp from "@/pages/Scalp";
import Signals from "@/pages/Signals";
import SignalsTimeline from "@/pages/SignalsTimeline";
import Strategies from "@/pages/Strategies";
import Swing from "@/pages/Swing";
import TelegramControl from "@/pages/TelegramControl";
import TelegramInsights from "@/pages/TelegramInsights";
import TelegramSettings from "@/pages/TelegramSettings";
import TelegramSignals from "@/pages/TelegramSignals";
import Trades from "@/pages/Trades";
import Watchlist from "@/pages/Watchlist";
import EnginesManager from "@/pages/EnginesManager";
import BacktestRunner from "@/pages/BacktestRunner";
import { BrowserRouter, NavLink, Route, Routes } from "react-router-dom";
import { Toaster } from "sonner";

export default function App() {
  const linkClass =
    "px-3 py-2 rounded-xl text-sm font-medium transition-colors hover:bg-zinc-100 dark:hover:bg-zinc-800";
  const activeClass =
    "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900";

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950">
        {/* Navigation Header */}
        <header className="sticky top-0 z-50 p-4 bg-white dark:bg-zinc-900 border-b border-zinc-200 dark:border-zinc-800 shadow-sm">
          <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3">
            {/* Logo & Nav Links */}
            <div className="flex items-center gap-4">
              <h1 className="text-xl font-bold text-zinc-900 dark:text-zinc-100">
                🤖 LEVIBOT
              </h1>
              <nav className="flex flex-wrap gap-2">
                {[
                  ["Overview", "/"],
                  ["ML", "/ml"],
                  ["Paper", "/paper"],
                  ["Signals", "/signals"],
                  ["Trades", "/trades"],
                  ["Strategies", "/strategies"],
                  ["Risk", "/risk"],
                  ["⚡ Scalp", "/scalp"],
                  ["📈 Daytrade", "/daytrade"],
                  ["🌊 Swing", "/swing"],
                  ["🎯 RSI+MACD", "/rsi-macd"],
                  ["👁️ Watchlist", "/watchlist"],
                  ["Analytics", "/analytics"],
                  ["AI Brain", "/ai-brain"],
                  ["Alerts", "/alerts"],
                  ["Telegram", "/telegram"],
                  ["Events", "/events"],
                  ["MEV", "/mev"],
                  ["NFT", "/nft"],
                  ["OnChain", "/onchain"],
                  ["Integrations", "/integrations"],
                  ["🔧 Engines", "/engines"],
                  ["📊 Backtest", "/backtest"],
                  ["Ops", "/ops"],
                ].map(([label, href]) => (
                  <NavLink
                    key={href}
                    to={href}
                    className={({ isActive }) =>
                      `${linkClass} ${
                        isActive
                          ? activeClass
                          : "text-zinc-700 dark:text-zinc-300"
                      }`
                    }
                  >
                    {label}
                  </NavLink>
                ))}
              </nav>
            </div>

            {/* Right Controls */}
            <div className="flex items-center gap-3">
              <ReplayBadge />
              <DarkModeToggle />
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto">
          <ErrorBoundary>
            <Routes>
              <Route path="/" element={<Overview />} />
              <Route path="/ml" element={<MLDashboard />} />
              <Route path="/paper" element={<Paper />} />
              <Route path="/signals" element={<Signals />} />
              <Route path="/signals-timeline" element={<SignalsTimeline />} />
              <Route path="/trades" element={<Trades />} />
              <Route path="/strategies" element={<Strategies />} />
              <Route path="/risk" element={<Risk />} />
              <Route path="/scalp" element={<Scalp />} />
              <Route path="/daytrade" element={<Daytrade />} />
              <Route path="/swing" element={<Swing />} />
              <Route path="/rsi-macd" element={<RsiMacd />} />
              <Route path="/watchlist" element={<Watchlist />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/ai-brain" element={<AIBrain />} />
              <Route path="/alerts" element={<Alerts />} />
              <Route path="/telegram" element={<TelegramSignals />} />
              <Route path="/telegram/control" element={<TelegramControl />} />
              <Route path="/telegram/insights" element={<TelegramInsights />} />
              <Route path="/telegram/settings" element={<TelegramSettings />} />
              <Route path="/events" element={<EventsTimeline />} />
              <Route path="/mev" element={<MEVFeed />} />
              <Route path="/nft" element={<NFTSniper />} />
              <Route path="/onchain" element={<OnChain />} />
              <Route path="/integrations" element={<Integrations />} />
              <Route path="/engines" element={<EnginesManager />} />
              <Route path="/backtest" element={<BacktestRunner />} />
              <Route path="/ops" element={<Ops />} />
            </Routes>
          </ErrorBoundary>
        </main>

        {/* Toast Notifications */}
        <Toaster
          position="bottom-right"
          toastOptions={{
            className:
              "dark:bg-zinc-900 dark:text-zinc-100 dark:border-zinc-800",
          }}
        />
      </div>
    </BrowserRouter>
  );
}
