import { useEffect, useState } from "react";

export default function TelegramSettings() {
  const [minAbs, setMinAbs] = useState(0.02);
  const [maxAge, setMaxAge] = useState(120);
  const [mode, setMode] = useState<"soft" | "hard">("soft");
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    fetch("/config")
      .then((r) => r.json())
      .then((cfg) => {
        const g = (cfg as any)?.features?.telegram?.evaluation?.gate || {};
        setMinAbs(g.min_abs_bias ?? 0.02);
        setMaxAge(g.max_age_min ?? 120);
        setMode((g.mode ?? "soft") as any);
      })
      .catch((err) => console.error(err));
  }, []);

  const save = async () => {
    setSaving(true);
    setStatus(null);
    try {
      const res = await fetch("/config", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          features: {
            telegram: {
              evaluation: {
                gate: { min_abs_bias: minAbs, max_age_min: maxAge, mode },
              },
            },
          },
        }),
      });
      if (!res.ok) throw new Error("save failed");
      setStatus("Saved successfully");
    } catch (err: any) {
      setStatus(err?.message || "Save failed");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-4 max-w-xl space-y-4">
      <h2 className="text-lg font-semibold">Telegram Gate Settings</h2>
      <div className="space-y-4 bg-zinc-900 rounded-2xl border border-zinc-800 p-4">
        <div className="flex items-center justify-between">
          <label className="text-sm">Min Abs Bias</label>
          <input
            type="number"
            step="0.001"
            value={minAbs}
            onChange={(e) => setMinAbs(parseFloat(e.target.value))}
            className="bg-zinc-900 border border-zinc-700 rounded-xl px-3 py-2 w-40"
          />
        </div>
        <div className="flex items-center justify-between">
          <label className="text-sm">Max Age (min)</label>
          <input
            type="number"
            value={maxAge}
            onChange={(e) => setMaxAge(parseInt(e.target.value || "0"))}
            className="bg-zinc-900 border border-zinc-700 rounded-xl px-3 py-2 w-40"
          />
        </div>
        <div className="flex items-center justify-between">
          <label className="text-sm">Mode</label>
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value as any)}
            className="bg-zinc-900 border border-zinc-700 rounded-xl px-3 py-2 w-40"
          >
            <option value="soft">soft</option>
            <option value="hard">hard</option>
          </select>
        </div>
        <button
          onClick={save}
          disabled={saving}
          className="px-4 py-2 rounded-2xl border border-blue-500 text-blue-400 hover:bg-blue-500/10 disabled:opacity-50"
        >
          {saving ? "Saving..." : "Save"}
        </button>
        {status && <p className="text-sm text-zinc-400">{status}</p>}
      </div>
    </div>
  );
}
