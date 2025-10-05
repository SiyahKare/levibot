import { useEffect, useState } from "react";
import { getL2Yields } from "../api";

type Row={chain:string; name:string; pool:string; apr:number};
export default function L2YieldsCard(){
  const [rows,setRows]=useState<Row[]>([]); const [err,setErr]=useState("");
  const fetchIt=async()=>{ try{ setErr(""); const j=await getL2Yields(); const out:Row[]=[]; (j.chains||[]).forEach((c:any)=> (c.protocols||[]).forEach((p:any)=> out.push({chain:c.name,name:p.name,pool:p.pool,apr:p.apr}))); setRows(out);}catch(e:any){setErr(e?.message||"err")} };
  useEffect(()=>{ fetchIt(); },[]);
  return (
    <div className="rounded-2xl shadow p-4 bg-white">
      <div className="flex items-center justify-between mb-2">
        <div className="font-semibold">L2 Yields</div>
        <button className="border rounded px-3 py-1 text-sm hover:bg-gray-50" onClick={fetchIt}>Refresh</button>
      </div>
      {err && <div className="text-red-500 text-sm">{err}</div>}
      <div className="overflow-auto max-h-64">
        <table className="w-full text-sm">
          <thead className="bg-gray-50"><tr className="text-left"><th className="p-2">Chain</th><th className="p-2">Protocol</th><th className="p-2">Pool</th><th className="p-2">APR%</th></tr></thead>
          <tbody>{rows.map((r,i)=>(<tr key={i} className="border-t"><td className="p-2">{r.chain}</td><td className="p-2">{r.name}</td><td className="p-2">{r.pool}</td><td className="p-2 font-semibold">{r.apr}</td></tr>))}</tbody>
        </table>
        {rows.length === 0 && <div className="text-gray-500 text-sm p-2">No data</div>}
      </div>
    </div>
  );
}
