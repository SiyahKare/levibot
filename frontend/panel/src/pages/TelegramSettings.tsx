import { useEffect, useState } from "react";

export default function TelegramSettings(){
  const [minAbs, setMinAbs] = useState(0.02);
  const [maxAge, setMaxAge] = useState(120);
  const [mode, setMode] = useState<"soft"|"hard">("soft");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetch("http://localhost:8000/config").then(r=>r.json()).then(cfg=>{
      const g = (cfg as any)?.features?.telegram?.evaluation?.gate || {};
      setMinAbs(g.min_abs_bias ?? 0.02);
      setMaxAge(g.max_age_min ?? 120);
      setMode((g.mode ?? "soft") as any);
    });
  }, []);

  const save = async () => {
    setSaving(true);
    await fetch("http://localhost:8000/config", {
      method:"PUT",
      headers:{ "Content-Type":"application/json" },
      body: JSON.stringify({ features:{ telegram:{ evaluation:{ gate:{ min_abs_bias:minAbs, max_age_min:maxAge, mode } } } } })
    });
    setSaving(false);
  };

  return (
    <div className="p-4 max-w-xl">
      <h2 className="text-lg font-semibold mb-4">Telegram Gate Settings</h2>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <label className="text-sm">Min Abs Bias</label>
          <input type="number" step="0.001" value={minAbs}
                 onChange={e=>setMinAbs(parseFloat(e.target.value))}
                 className="border rounded-xl px-3 py-2 w-40"/>
        </div>
        <div className="flex items-center justify-between">
          <label className="text-sm">Max Age (min)</label>
          <input type="number" value={maxAge}
                 onChange={e=>setMaxAge(parseInt(e.target.value||"0"))}
                 className="border rounded-xl px-3 py-2 w-40"/>
        </div>
        <div className="flex items-center justify-between">
          <label className="text-sm">Mode</label>
          <select value={mode} onChange={e=>setMode(e.target.value as any)}
                  className="border rounded-xl px-3 py-2 w-40">
            <option value="soft">soft</option>
            <option value="hard">hard</option>
          </select>
        </div>
        <button onClick={save} disabled={saving}
                className="px-4 py-2 rounded-2xl border shadow-sm">
          {saving ? "Saving..." : "Save"}
        </button>
      </div>
    </div>
  );
}
















