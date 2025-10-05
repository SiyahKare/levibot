import { useEffect, useState } from "react";

type TSignal = { ts:string; chat_title:string; symbol:string; side:string; confidence:number; trace_id:string };

export default function TelegramSignals(){
  const [rows,setRows] = useState<TSignal[]>([]);
  const [gate, setGate] = useState<{max_age_min:number}>({max_age_min: 120});
  const load = async () => {
    const r = await fetch("http://localhost:8000/telegram/signals");
    setRows(await r.json());
  };
  useEffect(()=>{ load(); const id=setInterval(load, 8000); return ()=>clearInterval(id); }, []);
  useEffect(()=>{ fetch("http://localhost:8000/config").then(r=>r.json()).then(cfg=>{
    const g = (cfg as any)?.features?.telegram?.evaluation?.gate || {};
    setGate({ max_age_min: g.max_age_min ?? 120 });
  }); },[]);
  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold mb-3">Telegram Signals</h2>
      <div className="overflow-x-auto rounded-2xl border">
        <table className="w-full text-sm">
          <thead><tr className="text-left text-zinc-500">
            <th className="py-2 px-3">Time</th><th>Group</th><th>Symbol</th><th>Side</th><th>Conf.</th><th>Status</th><th>Trace</th>
          </tr></thead>
          <tbody>
            {rows.map((r,i)=> (
              <tr key={i} className="border-t">
                <td className="py-2 px-3">{new Date(r.ts).toLocaleString()}</td>
                <td>{r.chat_title}</td>
                <td className="font-medium">{r.symbol}</td>
                <td>{r.side}</td>
                <td>{Math.round((r.confidence||0)*100)}%</td>
                <td>
                  {(() => {
                    const ageMin = (Date.now() - new Date(r.ts).getTime())/60000;
                    const fresh = ageMin <= gate.max_age_min;
                    return (
                      <span className={`px-2 py-0.5 rounded-xl border ${fresh ? "text-emerald-700 border-emerald-300" : "text-zinc-600 border-zinc-300"}`}>
                        {fresh ? "Fresh" : "Stale"}
                      </span>
                    );
                  })()}
                </td>
                <td>
                  <button
                    className="px-2 py-1 rounded-lg border"
                    onClick={()=> window.dispatchEvent(new CustomEvent("open-trace", { detail: r.trace_id }))}
                  >Trace</button>
                </td>
              </tr>
            ))}
            {!rows.length && <tr><td className="py-3 px-3 text-zinc-500" colSpan={7}>No signals yet</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
