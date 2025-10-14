/**
 * Replay Badge
 * Shows status of last nightly replay job
 */
import { api } from "@/lib/api";
import useSWR from "swr";

export function ReplayBadge() {
  const { data } = useSWR("/ops/replay/status", api.replayStatus, {
    refreshInterval: 60_000, // Check every minute
  });

  const ok = data?.ok && data?.status === "success";
  const status = data?.status || "unknown";

  return (
    <div
      className={`px-3 py-1 rounded-full text-xs font-medium ${
        ok
          ? "bg-emerald-100 text-emerald-700"
          : status === "no_report"
          ? "bg-zinc-100 text-zinc-600"
          : "bg-amber-100 text-amber-700"
      }`}
      title={data?.timestamp || "No replay data"}
    >
      Replay: {ok ? "✓ OK" : status === "no_report" ? "N/A" : "⚠ Check"}
    </div>
  );
}
