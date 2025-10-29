/**
 * Main App Component
 * Routing and navigation for LEVIBOT Panel
 */
import { Sidebar } from "@/components/Sidebar";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";
import AIBrain from "@/pages/AIBrain";
import Alerts from "@/pages/Alerts";
import Analytics from "@/pages/Analytics";
import BacktestRunner from "@/pages/BacktestRunner";
import Daytrade from "@/pages/Daytrade";
import EnginesManager from "@/pages/EnginesManager";
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
import TechnicalAnalysis from "@/pages/TechnicalAnalysis";
import TelegramControl from "@/pages/TelegramControl";
import TelegramInsights from "@/pages/TelegramInsights";
import TelegramSettings from "@/pages/TelegramSettings";
import TelegramSignals from "@/pages/TelegramSignals";
import Trades from "@/pages/Trades";
import Watchlist from "@/pages/Watchlist";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster } from "sonner";

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950">
        {/* Sidebar Navigation */}
        <Sidebar />

        {/* Main Content with left margin for sidebar */}
        <main className="lg:ml-64 p-6">
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
              <Route path="/technical" element={<TechnicalAnalysis />} />
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
