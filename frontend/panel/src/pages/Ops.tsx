/**
 * Ops Page
 * Operational controls: canary, kill switch, flags, version, snapshot
 */
import { api } from "@/lib/api";
import { useState } from "react";
import { toast } from "sonner";
import useSWR from "swr";

export default function Ops() {
  const { data: flags, mutate: mutateFlags } = useSWR(
    "/admin/flags",
    api.flags,
    { refreshInterval: 10_000 }
  );

  const { data: version } = useSWR("/ops/version", api.opsVersion);

  const { data: aiReason, mutate: mutateAiReason } = useSWR(
    "/admin/ai_reason/status",
    api.aiReasonStatus,
    { refreshInterval: 10_000 }
  );

  // Sprint-10 Epic-E: New kill switch API
  const { data: killStatus, mutate: mutateKillStatus } = useSWR(
    "/live/status",
    api.live.status,
    { refreshInterval: 5_000 }
  );

  const [busy, setBusy] = useState(false);
  const [adminKey, setAdminKey] = useState("");
  const [killReason, setKillReason] = useState("");

  const handleCanary = async (state: "on" | "off") => {
    setBusy(true);
    try {
      await api.canary(state);
      mutateFlags();
      toast.success(`Canary ${state.toUpperCase()}`);
    } catch (error: any) {
      console.error("Canary action failed:", error);
      toast.error(`Canary failed: ${error.message || "Unknown error"}`);
    } finally {
      setBusy(false);
    }
  };

  const handleKill = async () => {
    if (
      !confirm(
        "Are you sure you want to activate kill switch? This will stop all trading."
      )
    ) {
      return;
    }
    setBusy(true);
    try {
      await api.live.kill(true, killReason || "manual");
      await mutateKillStatus();
      mutateFlags();
      toast.error("🚨 Kill switch ACTIVATED - All trading stopped");
    } catch (error: any) {
      console.error("Kill failed:", error);
      toast.error(`Kill failed: ${error.message || "Unknown error"}`);
    } finally {
      setBusy(false);
    }
  };

  const handleUnkill = async () => {
    setBusy(true);
    try {
      await api.live.kill(false, "manual_reset");
      await mutateKillStatus();
      mutateFlags();
      toast.success("✅ Kill switch deactivated - Trading can resume");
    } catch (error: any) {
      console.error("Unkill failed:", error);
      toast.error(`Unkill failed: ${error.message || "Unknown error"}`);
    } finally {
      setBusy(false);
    }
  };

  const handleSnapshot = async () => {
    setBusy(true);
    try {
      const result = await api.takeSnapshot();
      toast.success(`Snapshot saved: ${result.path || "success"}`);
    } catch (error: any) {
      console.error("Snapshot failed:", error);
      toast.error(`Snapshot failed: ${error.message || "Unknown error"}`);
    } finally {
      setBusy(false);
    }
  };

  const handleLogin = async () => {
    if (!adminKey.trim()) {
      toast.error("Admin key required");
      return;
    }
    setBusy(true);
    try {
      const result = await api.adminLogin(adminKey);
      if (result.ok) {
        toast.success("✅ Logged in successfully");
        setAdminKey("");
      } else {
        toast.error("❌ Authentication failed");
      }
    } catch (error: any) {
      toast.error(`Login failed: ${error.message || "Unknown error"}`);
    } finally {
      setBusy(false);
    }
  };

  const handleLogout = async () => {
    setBusy(true);
    try {
      await api.adminLogout();
      toast.success("Logged out");
    } catch (error: any) {
      toast.error(`Logout failed: ${error.message || "Unknown error"}`);
    } finally {
      setBusy(false);
    }
  };

  const handleAiReason = async (state: "on" | "off") => {
    setBusy(true);
    try {
      await api.aiReasonToggle(state);
      mutateAiReason();
      toast.success(`AI Reasons ${state.toUpperCase()}`);
    } catch (error: any) {
      console.error("AI Reason toggle failed:", error);
      toast.error(`AI Reason failed: ${error.message || "Unknown error"}`);
    } finally {
      setBusy(false);
    }
  };

  const currentFlags = flags?.flags || {};
  const canaryMode = currentFlags.canary_mode;
  const killed = currentFlags.killed;

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-100">
          Operations
        </h1>
        <p className="text-zinc-600 dark:text-zinc-400 mt-2">
          System controls and runtime configuration
        </p>
      </div>

      {/* Admin Login */}
      <div className="p-6 rounded-2xl shadow bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800">
        <div className="flex items-center justify-between">
          <div>
            <div className="font-medium text-zinc-900 dark:text-zinc-100">
              🔐 Admin Authentication
            </div>
            <div className="text-xs text-zinc-500 dark:text-zinc-400 mt-1">
              Cookie-based login (IP allowlist enforced)
            </div>
          </div>
          <div className="flex gap-2 items-center">
            <input
              type="password"
              value={adminKey}
              onChange={(e) => setAdminKey(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleLogin()}
              placeholder="Admin key"
              className="px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100"
              disabled={busy}
            />
            <button
              onClick={handleLogin}
              disabled={busy}
              className="px-4 py-2 rounded-xl bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900 disabled:opacity-50"
            >
              Login
            </button>
            <button
              onClick={handleLogout}
              disabled={busy}
              className="px-4 py-2 rounded-xl bg-zinc-100 text-zinc-900 dark:bg-zinc-800 dark:text-zinc-100 disabled:opacity-50"
            >
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div
          className={`p-6 rounded-2xl shadow border-2 ${
            canaryMode
              ? "bg-amber-50 border-amber-300"
              : "bg-white border-zinc-200"
          }`}
        >
          <div className="text-sm text-zinc-600 mb-1">Canary Mode</div>
          <div
            className={`text-2xl font-bold ${
              canaryMode ? "text-amber-700" : "text-zinc-400"
            }`}
          >
            {canaryMode ? "ACTIVE" : "OFF"}
          </div>
        </div>

        <div
          className={`p-6 rounded-2xl shadow border-2 ${
            killed ? "bg-rose-50 border-rose-300" : "bg-white border-zinc-200"
          }`}
        >
          <div className="text-sm text-zinc-600 mb-1">Kill Switch</div>
          <div
            className={`text-2xl font-bold ${
              killed ? "text-rose-700" : "text-emerald-600"
            }`}
          >
            {killed ? "KILLED" : "ACTIVE"}
          </div>
        </div>

        <div className="p-6 rounded-2xl shadow bg-white border border-zinc-200">
          <div className="text-sm text-zinc-600 mb-1">API Version</div>
          <div className="text-2xl font-bold text-zinc-900">
            {version?.version || "—"}
          </div>
        </div>
      </div>

      {/* Control Buttons */}
      <div className="p-6 rounded-2xl shadow bg-white border border-zinc-200">
        <h2 className="text-lg font-semibold text-zinc-900 mb-4">
          System Controls
        </h2>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => handleCanary("on")}
            disabled={busy}
            className="px-6 py-3 rounded-xl font-medium bg-amber-500 text-white hover:bg-amber-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Canary ON
          </button>
          <button
            onClick={() => handleCanary("off")}
            disabled={busy}
            className="px-6 py-3 rounded-xl font-medium bg-zinc-900 text-white hover:bg-zinc-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Canary OFF
          </button>
          <button
            onClick={handleKill}
            disabled={busy}
            className="px-6 py-3 rounded-xl font-medium bg-rose-600 text-white hover:bg-rose-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            🚨 KILL
          </button>
          <button
            onClick={handleUnkill}
            disabled={busy}
            className="px-6 py-3 rounded-xl font-medium bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            ✅ UNKILL
          </button>
          <button
            onClick={handleSnapshot}
            disabled={busy}
            className="px-6 py-3 rounded-xl font-medium bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            📸 Take Snapshot
          </button>
        </div>
      </div>

      {/* AI Reason Control */}
      <div className="p-6 rounded-2xl shadow bg-white border border-zinc-200">
        <h2 className="text-lg font-semibold text-zinc-900 mb-4">
          AI Trade Reasons
        </h2>
        {aiReason ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-zinc-900">
                  Status: {aiReason.enabled ? "✅ Enabled" : "❌ Disabled"}
                </div>
                <div className="text-sm text-zinc-500 mt-1">
                  Timeout: {aiReason.timeout_s}s • Budget:{" "}
                  {aiReason.used_this_month.toLocaleString()} /{" "}
                  {aiReason.monthly_budget.toLocaleString()} tokens used
                </div>
                {aiReason.month && (
                  <div className="text-xs text-zinc-400 mt-1">
                    Month: {aiReason.month}
                  </div>
                )}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleAiReason("on")}
                  disabled={busy || aiReason.enabled}
                  className="px-4 py-2 rounded-xl font-medium bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  ON
                </button>
                <button
                  onClick={() => handleAiReason("off")}
                  disabled={busy || !aiReason.enabled}
                  className="px-4 py-2 rounded-xl font-medium bg-zinc-900 text-white hover:bg-zinc-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  OFF
                </button>
              </div>
            </div>
            <div className="pt-3 border-t border-zinc-200">
              <div className="text-sm text-zinc-600">
                AI reasons provide context-aware explanations for trades using
                market data and signal confidence. Budget prevents excessive API
                costs.
              </div>
            </div>
          </div>
        ) : (
          <div className="text-zinc-500">Loading AI reason status...</div>
        )}
      </div>

      {/* Flags */}
      <div className="p-6 rounded-2xl shadow bg-white border border-zinc-200">
        <h2 className="text-lg font-semibold text-zinc-900 mb-4">
          Runtime Flags
        </h2>
        <pre className="p-4 rounded-lg bg-zinc-50 text-xs overflow-auto max-h-96">
          {JSON.stringify(currentFlags, null, 2)}
        </pre>
      </div>

      {/* Version Info */}
      {version && (
        <div className="p-6 rounded-2xl shadow bg-zinc-50 border border-zinc-200">
          <h2 className="text-lg font-semibold text-zinc-900 mb-4">
            Build Info
          </h2>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-zinc-600">Version:</span>
              <span className="font-mono font-semibold">{version.version}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-zinc-600">Build Date:</span>
              <span className="font-mono">{version.build_date}</span>
            </div>
            {version.features && (
              <div className="mt-3">
                <div className="text-zinc-600 mb-2">Features:</div>
                <div className="flex flex-wrap gap-2">
                  {version.features.map((feat: string) => (
                    <span
                      key={feat}
                      className="px-2 py-1 rounded bg-zinc-200 text-zinc-700 text-xs"
                    >
                      {feat}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
