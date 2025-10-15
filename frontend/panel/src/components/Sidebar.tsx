/**
 * Modern Sidebar Navigation
 * Responsive with hamburger menu for mobile
 */
import { useState } from "react";
import { NavLink } from "react-router-dom";
import DarkModeToggle from "./DarkModeToggle";
import { ReplayBadge } from "./ReplayBadge";

interface NavItem {
  label: string;
  path: string;
  icon: string;
  category?: string;
}

const navItems: NavItem[] = [
  // Core
  { label: "Overview", path: "/", icon: "🏠", category: "Core" },
  { label: "ML Dashboard", path: "/ml", icon: "🧠", category: "Core" },
  { label: "Paper Trading", path: "/paper", icon: "💰", category: "Core" },

  // Trading
  { label: "Scalp", path: "/scalp", icon: "⚡", category: "Trading" },
  { label: "Daytrade", path: "/daytrade", icon: "📈", category: "Trading" },
  { label: "Swing", path: "/swing", icon: "🌊", category: "Trading" },
  { label: "RSI+MACD", path: "/rsi-macd", icon: "🎯", category: "Trading" },

  // Analysis
  { label: "Signals", path: "/signals", icon: "📡", category: "Analysis" },
  { label: "Analytics", path: "/analytics", icon: "📊", category: "Analysis" },
  { label: "AI Brain", path: "/ai-brain", icon: "🤖", category: "Analysis" },
  { label: "Watchlist", path: "/watchlist", icon: "👁️", category: "Analysis" },

  // Management
  { label: "Engines", path: "/engines", icon: "🔧", category: "Management" },
  { label: "Backtest", path: "/backtest", icon: "📊", category: "Management" },
  {
    label: "Strategies",
    path: "/strategies",
    icon: "📋",
    category: "Management",
  },
  { label: "Risk", path: "/risk", icon: "🛡️", category: "Management" },
  { label: "Trades", path: "/trades", icon: "💼", category: "Management" },

  // Advanced
  { label: "Alerts", path: "/alerts", icon: "🔔", category: "Advanced" },
  { label: "Telegram", path: "/telegram", icon: "✈️", category: "Advanced" },
  { label: "Events", path: "/events", icon: "📅", category: "Advanced" },
  { label: "OnChain", path: "/onchain", icon: "⛓️", category: "Advanced" },
  { label: "MEV", path: "/mev", icon: "⚡", category: "Advanced" },
  { label: "NFT", path: "/nft", icon: "🖼️", category: "Advanced" },
  {
    label: "Integrations",
    path: "/integrations",
    icon: "🔌",
    category: "Advanced",
  },
  { label: "Ops", path: "/ops", icon: "⚙️", category: "Advanced" },
];

export function Sidebar() {
  const [isOpen, setIsOpen] = useState(false);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(
    new Set(["Core", "Trading"])
  );

  const toggleCategory = (category: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(category)) {
      newExpanded.delete(category);
    } else {
      newExpanded.add(category);
    }
    setExpandedCategories(newExpanded);
  };

  const groupedItems = navItems.reduce((acc, item) => {
    const cat = item.category || "Other";
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(item);
    return acc;
  }, {} as Record<string, NavItem[]>);

  const categories = ["Core", "Trading", "Analysis", "Management", "Advanced"];

  return (
    <>
      {/* Mobile Hamburger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-white dark:bg-zinc-800 rounded-lg shadow-lg border border-zinc-200 dark:border-zinc-700"
        aria-label="Toggle menu"
      >
        <svg
          className="w-6 h-6 text-zinc-900 dark:text-zinc-100"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          {isOpen ? (
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          ) : (
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 6h16M4 12h16M4 18h16"
            />
          )}
        </svg>
      </button>

      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 h-screen w-64 bg-white dark:bg-zinc-900 border-r border-zinc-200 dark:border-zinc-800 z-40 transform transition-transform duration-300 ease-in-out overflow-y-auto ${
          isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        }`}
      >
        {/* Header */}
        <div className="p-4 border-b border-zinc-200 dark:border-zinc-800">
          <div className="flex items-center justify-between mb-3">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              🤖 LEVIBOT
            </h1>
            <button
              onClick={() => setIsOpen(false)}
              className="lg:hidden p-1 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
          <div className="flex items-center gap-2">
            <ReplayBadge />
            <DarkModeToggle />
          </div>
        </div>

        {/* Navigation */}
        <nav className="p-2 space-y-1">
          {categories.map((category) => {
            const items = groupedItems[category] || [];
            if (items.length === 0) return null;

            const isExpanded = expandedCategories.has(category);

            return (
              <div key={category} className="mb-2">
                {/* Category Header */}
                <button
                  onClick={() => toggleCategory(category)}
                  className="w-full flex items-center justify-between px-3 py-2 text-xs font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-lg transition-colors"
                >
                  <span>{category}</span>
                  <svg
                    className={`w-4 h-4 transition-transform ${
                      isExpanded ? "rotate-90" : ""
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </button>

                {/* Category Items */}
                {isExpanded && (
                  <div className="mt-1 space-y-0.5">
                    {items.map((item) => (
                      <NavLink
                        key={item.path}
                        to={item.path}
                        onClick={() => {
                          if (window.innerWidth < 1024) setIsOpen(false);
                        }}
                        className={({ isActive }) =>
                          `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                            isActive
                              ? "bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400"
                              : "text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800"
                          }`
                        }
                      >
                        <span className="text-lg">{item.icon}</span>
                        <span>{item.label}</span>
                      </NavLink>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
          <div className="text-xs text-zinc-500 dark:text-zinc-400 text-center">
            <div className="font-semibold">LeviBot v1.0</div>
            <div className="mt-1">Enterprise Trading Platform</div>
          </div>
        </div>
      </aside>
    </>
  );
}
