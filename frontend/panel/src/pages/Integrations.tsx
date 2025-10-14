import { useEffect, useState } from "react";

interface TelegramMessage {
  id: number;
  chat: string;
  date: string;
  text: string;
  impact?: number;
  confidence?: number;
}

export default function Integrations() {
  const [messages, setMessages] = useState<TelegramMessage[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMessages();
    const interval = setInterval(fetchMessages, 10000); // 10s refresh
    return () => clearInterval(interval);
  }, []);

  const fetchMessages = async () => {
    try {
      // For now, use mock data
      // TODO: Add API endpoint to read logs/telethon/*.jsonl
      setMessages([
        {
          id: 1,
          chat: "@crypto_alpha",
          date: new Date().toISOString(),
          text: "BTC breaking resistance at 65k",
          impact: 0.6,
          confidence: 0.8,
        },
        {
          id: 2,
          chat: "@defi_signals",
          date: new Date(Date.now() - 3600000).toISOString(),
          text: "New Uniswap V4 features announced",
          impact: 0.4,
          confidence: 0.7,
        },
      ]);

      setStats({
        total: 2,
        avgImpact: 0.5,
        lastUpdate: new Date().toISOString(),
        status: "connected",
      });

      setLoading(false);
    } catch (err) {
      console.error("Failed to fetch Telegram messages:", err);
      setLoading(false);
    }
  };

  const getImpactColor = (impact: number) => {
    if (impact > 0.5) return "text-green-400";
    if (impact > 0.2) return "text-green-300";
    if (impact < -0.5) return "text-red-400";
    if (impact < -0.2) return "text-red-300";
    return "text-gray-400";
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">🔗 Integrations</h1>
        <p className="text-gray-400 mt-1">
          External data sources and streaming feeds
        </p>
      </div>

      {/* Telegram Section */}
      <div className="rounded-xl border border-zinc-700 bg-zinc-800/50 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="text-3xl">✈️</div>
            <div>
              <h2 className="text-xl font-bold text-white">
                Telegram Live Feed
              </h2>
              <p className="text-sm text-gray-400">
                Real-time message ingestion from joined groups
              </p>
            </div>
          </div>

          {stats && (
            <div
              className={`px-4 py-2 rounded-lg ${
                stats.status === "connected"
                  ? "bg-green-500/10 border border-green-500"
                  : "bg-red-500/10 border border-red-500"
              }`}
            >
              <p
                className={`text-sm font-semibold ${
                  stats.status === "connected"
                    ? "text-green-400"
                    : "text-red-400"
                }`}
              >
                {stats.status === "connected" ? "🟢 Connected" : "🔴 Offline"}
              </p>
            </div>
          )}
        </div>

        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="rounded-lg bg-zinc-900 p-4">
              <p className="text-sm text-gray-400 mb-1">Total Messages</p>
              <p className="text-2xl font-bold text-white">{stats.total}</p>
            </div>
            <div className="rounded-lg bg-zinc-900 p-4">
              <p className="text-sm text-gray-400 mb-1">Avg Impact</p>
              <p
                className={`text-2xl font-bold ${getImpactColor(
                  stats.avgImpact
                )}`}
              >
                {(stats.avgImpact * 100).toFixed(0)}%
              </p>
            </div>
            <div className="rounded-lg bg-zinc-900 p-4">
              <p className="text-sm text-gray-400 mb-1">Last Update</p>
              <p className="text-sm font-mono text-white">
                {new Date(stats.lastUpdate).toLocaleTimeString()}
              </p>
            </div>
          </div>
        )}

        {/* Messages List */}
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-gray-400 mb-3">
            Recent Messages (Last 50)
          </h3>

          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
              <p className="ml-3 text-gray-400">Loading messages...</p>
            </div>
          ) : messages.length === 0 ? (
            <div className="rounded-lg bg-zinc-900 p-8 text-center">
              <p className="text-gray-400">No messages yet</p>
              <p className="text-sm text-gray-500 mt-2">
                Start the Telethon listener to see live messages
              </p>
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className="rounded-lg border border-zinc-700 bg-zinc-900 p-4"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono text-blue-400">
                      {msg.chat}
                    </span>
                    <span className="text-xs text-gray-500">
                      {new Date(msg.date).toLocaleTimeString()}
                    </span>
                  </div>

                  {msg.impact !== undefined && (
                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <p
                          className={`text-sm font-bold ${getImpactColor(
                            msg.impact
                          )}`}
                        >
                          {msg.impact > 0 ? "+" : ""}
                          {(msg.impact * 100).toFixed(0)}%
                        </p>
                        <p className="text-xs text-gray-500">
                          {msg.confidence
                            ? `${(msg.confidence * 100).toFixed(0)}% conf`
                            : ""}
                        </p>
                      </div>
                    </div>
                  )}
                </div>

                <p className="text-sm text-gray-300">{msg.text}</p>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Setup Instructions */}
      <div className="rounded-xl border border-zinc-700 bg-zinc-800/50 p-6">
        <h3 className="text-lg font-bold text-white mb-4">
          📖 Setup Instructions
        </h3>

        <div className="space-y-4 text-sm text-gray-300">
          <div>
            <p className="font-semibold text-white mb-2">
              1. Get Telegram API Credentials
            </p>
            <p>
              Visit{" "}
              <code className="bg-zinc-900 px-2 py-1 rounded">
                my.telegram.org
              </code>{" "}
              and create an API app
            </p>
          </div>

          <div>
            <p className="font-semibold text-white mb-2">
              2. Configure Environment Variables
            </p>
            <pre className="bg-zinc-900 p-3 rounded overflow-x-auto text-xs">
              {`TG_API_ID=123456
TG_API_HASH=your_api_hash
TG_PHONE=+1234567890
TG_SESSION_NAME=levibot_user
TG_WATCH_LIST=@group1,@group2  # or leave empty for all`}
            </pre>
          </div>

          <div>
            <p className="font-semibold text-white mb-2">3. First Login</p>
            <pre className="bg-zinc-900 p-3 rounded overflow-x-auto text-xs">
              {`python backend/integrations/telethon_listener.py`}
            </pre>
            <p className="text-gray-400 mt-2">
              Enter SMS code when prompted. Session will be saved.
            </p>
          </div>

          <div>
            <p className="font-semibold text-white mb-2">4. Start in Docker</p>
            <pre className="bg-zinc-900 p-3 rounded overflow-x-auto text-xs">
              {`docker compose up -d --build tg-listener`}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}
