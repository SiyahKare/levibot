import { useEffect, useState } from 'react'

type Ev = { ts:string; event_type:string; payload:any }

export default function NFTSniper(){
  const [rows,setRows] = useState<Ev[]>([])
  const [minUsd,setMinUsd] = useState<number>(100)
  const [rare,setRare] = useState<number>(0.9)
  const load = async () => {
    const r = await fetch(`http://localhost:8000/events?event_type=NFT_SNIPE_CANDIDATE&limit=200`)
    const data:Ev[] = await r.json()
    setRows(data.filter(d=> (d.payload?.ask||0) >= minUsd && (d.payload?.rare_score||0) >= rare))
  }
  useEffect(()=>{ load(); const id=setInterval(load, 6000); return ()=>clearInterval(id) },[minUsd, rare])
  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold mb-3">NFT Sniper</h2>
      <div className="flex items-center gap-3 mb-3">
        <label className="text-sm">Min Ask (USD)
          <input className="ml-2 bg-zinc-800 px-2 py-1 rounded w-24" type="number" value={minUsd} onChange={e=>setMinUsd(Number(e.target.value)||0)} />
        </label>
        <label className="text-sm">Rare ≥
          <input className="ml-2 bg-zinc-800 px-2 py-1 rounded w-24" type="number" step="0.01" value={rare} onChange={e=>setRare(Number(e.target.value)||0)} />
        </label>
      </div>
      <div className="overflow-x-auto rounded-2xl border">
        <table className="w-full text-sm">
          <thead><tr className="text-left text-zinc-500"><th className="py-2 px-3">Time</th><th>Collection</th><th>Token</th><th>Ask</th><th>Floor</th><th>Rare</th><th>Spread%</th><th>Provider</th></tr></thead>
          <tbody>
            {rows.map((r,i)=> (
              <tr key={i} className="border-t">
                <td className="py-2 px-3">{new Date(r.ts).toLocaleTimeString()}</td>
                <td>{r.payload?.collection}</td>
                <td>{r.payload?.tokenId}</td>
                <td>${r.payload?.ask?.toFixed?.(2) ?? r.payload?.ask}</td>
                <td>${r.payload?.floor?.toFixed?.(2) ?? r.payload?.floor}</td>
                <td>{(r.payload?.rare_score||0).toFixed(2)}</td>
                <td>{(r.payload?.spread_pct||0).toFixed(2)}%</td>
                <td>{r.payload?.provider}</td>
              </tr>
            ))}
            {!rows.length && <tr><td className="py-3 px-3 text-zinc-500" colSpan={8}>No candidates</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}













