import { useState, useEffect } from "react";
import AddToDataset from "../components/AddToDataset";
import { getRiskPolicy, setRiskPolicy } from "../api";

export default function Signals() {
  const [text, setText] = useState("");
  const [thr, setThr] = useState(0.75);
  const [policy, setPolicy] = useState<string>("moderate");
  const [choices, setChoices] = useState<string[]>(["conservative","moderate","aggressive"]);
  const [note, setNote] = useState<string>("");
  const [log, setLog] = useState<any[]>([]);
  const [res, setRes] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getRiskPolicy().then(j => {
      setPolicy(j.current);
      setChoices(j.choices || choices);
    }).catch(()=>{ /* ignore */ });
  }, []);

  const score = async () => {
    if (!text.trim()) return;
    setLoading(true);
    try {
      const q = new URLSearchParams({ text }).toString();
      const r = await fetch(`/signals/score?${q}`, { method: "POST" });
      const j = await r.json();
      setRes(j);
      setLog((cur) => [{ at: Date.now(), text, ...j }, ...cur].slice(0, 10));
    } finally {
      setLoading(false);
    }
  };

  const apply = async () => {
    try {
      setNote("Saving…");
      const j = await setRiskPolicy(policy /* , optionalApiKeyIfNeeded */);
      setPolicy(j.current);
      setNote("Saved ✅");
      setTimeout(()=>setNote(""), 1500);
    } catch (e:any) {
      setNote(e?.message || "error");
    }
  };

  const autoRoute = res && res.confidence >= thr && res.label !== "NO-TRADE";

  return (
    <div className="p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Signal Scoring</h1>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">Risk Policy</span>
          <select className="border rounded px-2 py-1 text-sm" value={policy} onChange={e=>setPolicy(e.target.value)}>
            {choices.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <button className="border rounded px-3 py-1 text-sm" onClick={apply}>Apply</button>
          {note && <span className="text-xs text-gray-500 ml-2">{note}</span>}
        </div>
      </div>

      <textarea
        className="border rounded w-full p-2 h-32"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Paste Telegram message…"
      />

      <div className="flex items-center gap-4">
        <button
          className="border rounded px-3 py-1 disabled:opacity-50"
          disabled={loading || !text.trim()}
          onClick={score}
        >
          {loading ? "Scoring…" : "Score"}
        </button>
        <div className="text-sm flex items-center gap-2">
          <span>
            Auto-route threshold: <b>{thr.toFixed(2)}</b>
          </span>
          <input
            type="range"
            min={0.5}
            max={0.95}
            step={0.01}
            value={thr}
            onChange={(e) => setThr(parseFloat(e.target.value))}
            className="ml-2"
          />
        </div>
      </div>

      {res && (
        <div className="border rounded p-3 text-sm space-y-1">
          <div>
            label: <b>{res.label}</b>
          </div>
          <div>
            confidence: <b>{res.confidence}</b>
          </div>
          {res?.reasons && (
            <div className="mt-2 text-xs text-gray-600">
              {Array.isArray(res.reasons) ? res.reasons.join(" • ") : String(res.reasons)}
            </div>
          )}
          {res?.fe && (
            <div className="mt-2 text-xs border-t pt-2">
              <div>symbols: <b>{Array.isArray(res.fe.symbols) ? res.fe.symbols.join(", ") : "-"}</b></div>
              <div>tp/sl/size: <b>{res.fe.tp ?? "-"}</b> / <b>{res.fe.sl ?? "-"}</b> / <b>{res.fe.size ?? "-"}</b></div>
            </div>
          )}
          <div className={`mt-2 ${autoRoute ? "text-green-600" : "text-gray-500"}`}>
            {autoRoute
              ? "Would auto-route to paper order ✅"
              : "Below threshold / NO-TRADE — no route"}
          </div>
        </div>
      )}

      {res && (
        <div className="border rounded p-3 text-sm">
          <div className="font-medium mb-2">Add to dataset</div>
          <AddToDataset defaultText={text} defaultLabel={res.label} />
        </div>
      )}

      <div>
        <h2 className="font-medium mt-4 mb-2">Recent (10)</h2>
        <div className="overflow-auto border rounded">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="p-2 text-left w-[160px]">Time</th>
                <th className="p-2 text-left">Text</th>
                <th className="p-2">Label</th>
                <th className="p-2">Conf</th>
              </tr>
            </thead>
            <tbody>
              {log.map((r, i) => (
                <tr key={i} className="border-t">
                  <td className="p-2 whitespace-nowrap">{new Date(r.at).toLocaleString()}</td>
                  <td className="p-2">{r.text}</td>
                  <td className="p-2">{r.label}</td>
                  <td className="p-2">{Number(r.confidence).toFixed(2)}</td>
                </tr>
              ))}
              {log.length === 0 && (
                <tr>
                  <td className="p-2 text-gray-500" colSpan={4}>
                    No entries
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

