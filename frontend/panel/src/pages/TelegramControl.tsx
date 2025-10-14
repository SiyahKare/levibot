import { useState } from "react";
import useSWR from "swr";

interface TelegramStatus {
  ok: boolean;
  bot_configured: boolean;
  alert_chat_configured: boolean;
  connection: string;
}

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export default function TelegramControl() {
  const [testMessage, setTestMessage] = useState(
    "🚀 LeviBot test message from panel!"
  );
  const [sending, setSending] = useState(false);
  const [sendResult, setSendResult] = useState<string | null>(null);

  const { data: status } = useSWR<TelegramStatus>("/telegram/status", fetcher, {
    refreshInterval: 10000,
  });

  const sendTestAlert = async () => {
    setSending(true);
    setSendResult(null);
    try {
      // Backend endpoint to send Telegram message
      const r = await fetch("/telegram/test-alert", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: testMessage }),
      });

      if (r.ok) {
        setSendResult("✅ Test alert sent successfully!");
      } else {
        const err = await r.text();
        setSendResult(`❌ Failed: ${err}`);
      }
    } catch (e) {
      setSendResult(`❌ Error: ${e}`);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
          🤖 Telegram Control
          <span className="text-sm font-normal text-gray-400 bg-zinc-800 px-3 py-1 rounded-full">
            Bot Integration
          </span>
        </h1>
        <p className="text-gray-400 mt-2">
          Manage Telegram bot alerts and commands
        </p>
      </div>

      {/* Bot Status */}
      <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-6">
        <h2 className="text-xl font-bold text-white mb-4">📡 Bot Status</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-zinc-800 rounded-lg">
            <div className="text-xs uppercase text-zinc-500 mb-2">
              Connection
            </div>
            <div
              className={`text-lg font-bold ${
                status?.connection === "active"
                  ? "text-green-400"
                  : "text-red-400"
              }`}
            >
              {status?.connection === "active"
                ? "🟢 Active"
                : "🔴 Not Configured"}
            </div>
          </div>
          <div className="p-4 bg-zinc-800 rounded-lg">
            <div className="text-xs uppercase text-zinc-500 mb-2">
              Bot Token
            </div>
            <div className="text-sm font-mono text-zinc-300">
              {status?.bot_configured ? "✅ Configured" : "❌ Not configured"}
            </div>
          </div>
          <div className="p-4 bg-zinc-800 rounded-lg">
            <div className="text-xs uppercase text-zinc-500 mb-2">
              Alert Chat
            </div>
            <div className="text-sm font-mono text-zinc-300">
              {status?.alert_chat_configured
                ? "✅ Configured"
                : "❌ Not configured"}
            </div>
          </div>
        </div>
      </div>

      {/* Available Commands */}
      <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-6">
        <h2 className="text-xl font-bold text-white mb-4">
          ⚡ Available Commands
        </h2>
        <div className="space-y-2">
          {[
            { cmd: "/start", desc: "Start LeviBot trading automation" },
            { cmd: "/stop", desc: "Stop LeviBot and close all positions" },
            { cmd: "/status", desc: "Get current system status and metrics" },
            {
              cmd: "/setleverage N",
              desc: "Set leverage multiplier (e.g., /setleverage 3)",
            },
          ].map((item) => (
            <div
              key={item.cmd}
              className="flex items-start gap-3 p-3 bg-zinc-800 rounded-lg"
            >
              <code className="text-cyan-400 font-mono font-bold">
                {item.cmd}
              </code>
              <span className="text-zinc-300 text-sm">{item.desc}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Test Alert */}
      <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-6">
        <h2 className="text-xl font-bold text-white mb-4">🧪 Test Alert</h2>
        <p className="text-gray-400 text-sm mb-4">
          Send a test message to your configured Telegram alert chat
        </p>

        <textarea
          className="w-full p-3 bg-zinc-800 rounded-lg border border-zinc-700 text-white placeholder-zinc-500 focus:ring-blue-500 focus:border-blue-500 mb-3"
          rows={3}
          value={testMessage}
          onChange={(e) => setTestMessage(e.target.value)}
          placeholder="Enter test message..."
        />

        <button
          onClick={sendTestAlert}
          disabled={sending || !testMessage.trim()}
          className="px-6 py-2 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white font-semibold rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {sending ? "Sending..." : "📤 Send Test Alert"}
        </button>

        {sendResult && (
          <div
            className={`mt-4 p-3 rounded-lg ${
              sendResult.startsWith("✅")
                ? "bg-green-900/30 border border-green-700 text-green-300"
                : "bg-red-900/30 border border-red-700 text-red-300"
            }`}
          >
            {sendResult}
          </div>
        )}
      </div>

      {/* Alert Configuration */}
      <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-6">
        <h2 className="text-xl font-bold text-white mb-4">
          ⚙️ Alert Configuration
        </h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-zinc-400 mb-2">
              Alert Targets
            </label>
            <div className="flex flex-wrap gap-2">
              {["Telegram", "Discord", "Slack"].map((target) => (
                <label
                  key={target}
                  className="flex items-center gap-2 px-4 py-2 bg-zinc-800 rounded-lg cursor-pointer hover:bg-zinc-700 transition"
                >
                  <input
                    type="checkbox"
                    defaultChecked={target === "Telegram"}
                    className="form-checkbox text-cyan-600"
                  />
                  <span className="text-white">{target}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-zinc-400 mb-2">
              Alert Severity Filter
            </label>
            <select className="w-full md:w-64 px-4 py-2 bg-zinc-800 rounded-lg border border-zinc-700 text-white focus:ring-blue-500 focus:border-blue-500">
              <option value="info">Info and above</option>
              <option value="low">Low and above</option>
              <option value="medium">Medium and above</option>
              <option value="high" selected>
                High and above
              </option>
              <option value="critical">Critical only</option>
            </select>
          </div>

          <button className="px-6 py-2 bg-zinc-700 hover:bg-zinc-600 text-white font-semibold rounded-lg transition">
            💾 Save Configuration
          </button>
        </div>
      </div>
    </div>
  );
}
