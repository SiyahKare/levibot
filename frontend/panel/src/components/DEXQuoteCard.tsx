import { useEffect, useState } from "react";
import { getDexQuote } from "../api";

export default function DEXQuoteCard() {
  const [sell,setSell]=useState("ETH"); const [buy,setBuy]=useState("USDC");
  const [amount,setAmount]=useState(0.1); const [price,setPrice]=useState<number|null>(null);
  const [loading,setLoading]=useState(false); const [err,setErr]=useState<string>("");

  const fetchIt=async()=>{ try{ setLoading(true); setErr(""); const j=await getDexQuote({sell, buy, amount}); setPrice(j.price);}catch(e:any){setErr(e?.message||"err")}finally{setLoading(false);} };
  useEffect(()=>{ fetchIt(); /* auto */},[]);

  return (
    <div className="rounded-2xl shadow p-4 bg-white">
      <div className="font-semibold mb-2">DEX Quote</div>
      <div className="flex gap-2 mb-2 flex-wrap">
        <input className="border rounded px-2 py-1 w-20" value={sell} onChange={e=>setSell(e.target.value.toUpperCase())} placeholder="ETH"/>
        <span className="self-center">→</span>
        <input className="border rounded px-2 py-1 w-20" value={buy} onChange={e=>setBuy(e.target.value.toUpperCase())} placeholder="USDC"/>
        <input className="border rounded px-2 py-1 w-24" type="number" step="0.01" value={amount} onChange={e=>setAmount(parseFloat(e.target.value||"0"))}/>
        <button onClick={fetchIt} className="border rounded px-3 py-1 hover:bg-gray-50" disabled={loading}>{loading?"...":"Get"}</button>
      </div>
      {err && <div className="text-red-500 text-sm">{err}</div>}
      <div className="text-sm">{price!==null ? <>Price: <b className="text-lg">{price.toFixed(2)}</b></> : "—"}</div>
    </div>
  );
}
