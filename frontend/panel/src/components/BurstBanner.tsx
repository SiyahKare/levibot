import { useEffect, useState } from "react";

export default function BurstBanner(){
  const [msg, setMsg] = useState<string|null>(null);
  useEffect(()=>{
    let cancel=false;
    const tick = async () => {
      const since = new Date(Date.now()-15*60*1000).toISOString();
      const res = await fetch(`http://localhost:8000/events?since_iso=${encodeURIComponent(since)}&limit=100`);
      const rows = await res.json();
      const last = rows.find((e:any)=> e.event_type === "ALERT_TELEGRAM_BURST");
      if(!cancel && last){
        const p = last.payload || {};
        setMsg(`🚨 Burst: ${p.symbol} ${p.side} ×${p.count} (rep ${Math.round((p.avg_reputation||0)*100)}%)`);
        setTimeout(()=>setMsg(null), 12000);
      }
    };
    tick(); const id=setInterval(tick, 10000);
    return ()=>{ cancel=true; clearInterval(id); };
  },[]);
  if(!msg) return null;
  return <div className="m-3 p-3 rounded-2xl border bg-amber-50 text-amber-800">{msg}</div>;
}
















