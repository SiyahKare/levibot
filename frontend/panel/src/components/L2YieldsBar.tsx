import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { getL2Yields } from "../api";

type Row={chain:string; protocol:string; apr:number};
export default function L2YieldsBar(){
  const [rows,setRows]=useState<Row[]>([]);
  const [loading,setLoading]=useState(false);
  const [err,setErr]=useState("");

  const fetchIt=async()=>{ try{
    setLoading(true); setErr("");
    const j=await getL2Yields();
    const out:Row[]=[]; (j.chains||[]).forEach((c:any)=>(c.protocols||[]).forEach((p:any)=>out.push({chain:c.name, protocol:`${p.name} (${p.pool})`, apr:Number(p.apr||0)})));
    setRows(out);
  }catch(e:any){ setErr(e?.message||"err"); } finally { setLoading(false); }};

  useEffect(()=>{ fetchIt(); const id=setInterval(fetchIt,30000); return ()=>clearInterval(id); },[]);

  return (
    <div className="rounded-2xl shadow p-4 bg-white">
      <div className="flex items-center justify-between mb-2">
        <div className="font-semibold">L2 Yields — APR %</div>
        <button className="border rounded px-3 py-1 text-sm hover:bg-gray-50" onClick={fetchIt} disabled={loading}>{loading?"...":"Refresh"}</button>
      </div>
      {err && <div className="text-red-500 text-sm mb-2">{err}</div>}
      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows}>
            <XAxis dataKey="protocol" hide />
            <YAxis/>
            <Legend/>
            <Tooltip formatter={(v)=>Number(v).toFixed(2)+"%"} />
            <Bar dataKey="apr" name="APR%" fill="#3b82f6"/>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="text-xs mt-1 opacity-60">Toplam: {rows.length} havuz | Auto-refresh: 30s</div>
    </div>
  );
}
