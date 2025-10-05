import { useState } from "react";

export default function AddToDataset({
  defaultText = "",
  defaultLabel = "BUY",
}: {
  defaultText?: string;
  defaultLabel?: string;
}) {
  const [t, setT] = useState(defaultText);
  const [lbl, setLbl] = useState(defaultLabel);
  const [msg, setMsg] = useState("");

  const save = async () => {
    setMsg("");
    try {
      const body = JSON.stringify({ text: t, label: lbl });
      const r = await fetch("/ml/dataset/append", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body,
      });
      if (!r.ok) throw new Error("append failed");
      setMsg("Saved ✅");
    } catch (e: any) {
      setMsg(e.message || "error");
    }
  };

  return (
    <div className="space-y-2">
      <textarea
        className="border rounded w-full p-2 h-24"
        value={t}
        onChange={(e) => setT(e.target.value)}
      />
      <div className="flex items-center gap-2">
        <select
          className="border rounded px-2 py-1"
          value={lbl}
          onChange={(e) => setLbl(e.target.value)}
        >
          <option>BUY</option>
          <option>SELL</option>
          <option>NO-TRADE</option>
        </select>
        <button className="border rounded px-3 py-1" onClick={save}>
          Append
        </button>
        {msg && <div className="text-xs text-gray-600">{msg}</div>}
      </div>
    </div>
  );
}



