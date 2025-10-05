import { useEffect, useState } from "react";
import { getNftFloor, getNftSnipePlan } from "../api";

export default function NFTFloorCard() {
  const [col,setCol]=useState("miladymaker");
  const [floor,setFloor]=useState<number|null>(null);
  const [budget,setBudget]=useState(300); const [disc,setDisc]=useState(12);
  const [target,setTarget]=useState<number|null>(null); const [err,setErr]=useState("");

  const fetchFloor=async()=>{ try{ setErr(""); const j=await getNftFloor(col); setFloor(j.floor ?? null);}catch(e:any){setErr(e?.message||"err")} };
  const plan=async()=>{ try{ setErr(""); const j=await getNftSnipePlan(col,budget,disc); setTarget(j.target_usd ?? null);}catch(e:any){setErr(e?.message||"err")} };

  useEffect(()=>{ fetchFloor(); },[]);
  return (
    <div className="rounded-2xl shadow p-4 bg-white">
      <div className="font-semibold mb-2">NFT Floor & Snipe</div>
      <div className="flex flex-wrap gap-2 mb-2">
        <input className="border rounded px-2 py-1 flex-1 min-w-[120px]" value={col} onChange={e=>setCol(e.target.value)} placeholder="collection"/>
        <button className="border rounded px-3 py-1 hover:bg-gray-50" onClick={fetchFloor}>Floor</button>
      </div>
      <div className="flex flex-wrap gap-2 mb-2">
        <input className="border rounded px-2 py-1 w-24" type="number" value={budget} onChange={e=>setBudget(parseFloat(e.target.value||"0"))} placeholder="budget"/>
        <input className="border rounded px-2 py-1 w-20" type="number" value={disc} onChange={e=>setDisc(parseFloat(e.target.value||"0"))} placeholder="%"/>
        <button className="border rounded px-3 py-1 hover:bg-gray-50" onClick={plan}>Plan</button>
      </div>
      {err && <div className="text-red-500 text-sm">{err}</div>}
      <div className="text-sm">Floor: <b className="text-lg">{floor !== null ? `$${floor.toFixed(2)}` : "—"}</b></div>
      <div className="text-sm">Target@{disc}%: <b className="text-lg">{target !== null ? `$${target.toFixed(2)}` : "—"}</b></div>
    </div>
  );
}
