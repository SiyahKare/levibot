import { useEffect, useState, useRef } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { getDexQuoteSeries } from "../api";

export default function DEXSparkline(){
  const [data,setData]=useState<{t:number;p:number}[]>([]);
  const [sell,setSell]=useState("ETH"); const [buy,setBuy]=useState("USDC");
  const [loading,setLoading]=useState(false);
  const timer=useRef<number|undefined>(undefined);

  const load = async () => {
    setLoading(true);
    try { setData(await getDexQuoteSeries(sell,buy,24)); }
    finally { setLoading(false); }
  };

  useEffect(()=>{ load(); timer.current=window.setInterval(load, 30000); return ()=>clearInterval(timer.current); },[sell,buy]);

  return (
    <div className="rounded-2xl shadow p-4 bg-white">
      <div className="flex items-center justify-between mb-2">
        <div className="font-semibold">DEX Price — {sell}/{buy}</div>
        <div className="flex gap-2">
          <input className="border rounded px-2 py-1 w-20 text-sm" value={sell} onChange={e=>setSell(e.target.value.toUpperCase())} placeholder="ETH"/>
          <input className="border rounded px-2 py-1 w-20 text-sm" value={buy} onChange={e=>setBuy(e.target.value.toUpperCase())} placeholder="USDC"/>
          <button className="border rounded px-3 py-1 text-sm hover:bg-gray-50" onClick={load} disabled={loading}>{loading?"...":"Refresh"}</button>
        </div>
      </div>
      <div className="h-40">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <XAxis dataKey="t" hide />
            <YAxis domain={["auto","auto"]} width={50}/>
            <Tooltip formatter={(v)=>Number(v).toFixed(2)} labelFormatter={()=>""}/>
            <Line type="monotone" dataKey="p" dot={false} strokeWidth={2} stroke="#10b981"/>
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="text-xs mt-1 opacity-60">Auto-refresh: 30s | Points: {data.length}</div>
    </div>
  );
}
