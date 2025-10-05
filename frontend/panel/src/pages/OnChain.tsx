import { useEffect, useState } from 'react'

type Ev = { ts:string; event_type:string; payload:any }

export default function OnChain(){
  const [rows,setRows] = useState<Ev[]>([])
  const [kind,setKind] = useState<string>('')
  const load = async () => {
    const et = 'ONCHAIN_SIGNAL'
    const r = await fetch(`http://localhost:8000/events?event_type=${et}&limit=200`)
    const data:Ev[] = await r.json()
    setRows(kind ? data.filter(d=> (d.payload?.kind||'')===kind) : data)
  }
  useEffect(()=>{ load(); const id=setInterval(load, 5000); return ()=>clearInterval(id) },[kind])
  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold mb-3">On-Chain Signals</h2>
      <div className="flex gap-2 mb-2">
        <select className="bg-zinc-800 px-2 py-1 rounded" value={kind} onChange={e=>setKind(e.target.value)}>
          <option value="">All</option>
          <option value="univ3_pool_created">UniswapV3: PoolCreated</option>
          <option value="erc20_transfer">ERC20 Transfer</option>
        </select>
      </div>
      <div className="overflow-x-auto rounded-2xl border">
        <table className="w-full text-sm">
          <thead><tr className="text-left text-zinc-500">
            <th className="py-2 px-3">Time</th><th>Kind</th><th>Chain</th><th>Tx</th>
          </tr></thead>
          <tbody>
            {rows.map((r,i)=> (
              <tr key={i} className="border-t">
                <td className="py-2 px-3">{new Date(r.ts).toLocaleTimeString()}</td>
                <td>{r.payload?.kind}</td>
                <td>{r.payload?.chain}</td>
                <td><a className="text-sky-400" href={`https://etherscan.io/tx/${r.payload?.tx_hash}`} target="_blank">trace</a></td>
              </tr>
            ))}
            {!rows.length && <tr><td className="py-3 px-3 text-zinc-500" colSpan={4}>No data</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}













