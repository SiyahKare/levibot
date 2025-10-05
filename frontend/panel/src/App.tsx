import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useEffect, useState } from 'react'
import TelegramSignals from './pages/TelegramSignals'
import TelegramInsights from './pages/TelegramInsights'
import TelegramSettings from './pages/TelegramSettings'
import OnChain from './pages/OnChain'
import MEVFeed from './pages/MEVFeed'
import NFTSniper from './pages/NFTSniper'
import Trades from './pages/Trades'
import Signals from './pages/Signals'
import SignalsTimeline from './pages/SignalsTimeline'
import BurstBanner from './components/BurstBanner'
import DEXQuoteCard from './components/DEXQuoteCard'
import NFTFloorCard from './components/NFTFloorCard'
import L2YieldsCard from './components/L2YieldsCard'
import DEXSparkline from './components/DEXSparkline'
import L2YieldsBar from './components/L2YieldsBar'
import type { Event } from './types'
import { download } from './lib/download'

const data = Array.from({ length: 30 }).map((_, i) => ({ t: i, eq: 10000 * (1 + 0.01 * Math.sin(i / 5)) }))

export default function App() {
  const [traceId, setTraceId] = useState('')
  const [events, setEvents] = useState<Event[]>([])

  async function loadEvents(id: string) {
    const r = await fetch(`http://localhost:8000/events?trace_id=${id}`)
    const data = await r.json()
    setEvents(data)
  }

  return (
    <div className="min-h-screen bg-black text-white p-4">
      <h1 className="text-2xl font-bold mb-4">LeviBot — ETH-led Altseason Radar</h1>
      <BurstBanner />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-4 bg-zinc-900 rounded">
          <h2 className="font-semibold mb-2">Equity</h2>
          <div style={{ width: '100%', height: 240 }}>
            <ResponsiveContainer>
              <LineChart data={data}>
                <XAxis dataKey="t" hide/>
                <YAxis hide/>
                <Tooltip/>
                <Line type="monotone" dataKey="eq" stroke="#10b981" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="p-4 bg-zinc-900 rounded">
          <h2 className="font-semibold mb-2">Controls</h2>
          <div className="flex items-center gap-2">
            <button className="px-3 py-2 bg-emerald-600 rounded">Start</button>
            <button className="px-3 py-2 bg-rose-600 rounded">Stop</button>
          </div>
          <div className="mt-4">
            <h3 className="font-semibold mb-2">Trace View</h3>
            <div className="flex gap-2 mb-2">
              <input className="bg-zinc-800 px-2 py-1 rounded" placeholder="trace_id" value={traceId} onChange={e=>setTraceId(e.target.value)} />
              <button className="px-3 py-1 bg-sky-600 rounded" onClick={()=>loadEvents(traceId)}>Load</button>
              <button className="px-3 py-1 bg-zinc-700 rounded border border-zinc-600" onClick={()=>download(`http://localhost:8000/events?trace_id=${traceId}&format=jsonl`, `${traceId||'trace'}.jsonl`)}>Export JSONL</button>
            </div>
            <div className="max-h-56 overflow-auto text-sm">
              {events.map((ev, i)=> (
                <div key={i} className="py-2 border-b border-zinc-800">
                  <div className="flex items-center gap-2">
                    <span className="text-zinc-400">{new Date(ev.ts).toLocaleTimeString()}</span>
                    <span className="px-2 py-0.5 bg-zinc-800 rounded">{ev.event_type}</span>
                  </div>
                  {ev.event_type === 'SIGNAL_SCORE' && (
                    <div className="mt-1 grid grid-cols-2 gap-2">
                      <div>Trend: <b>{Math.round((ev.payload?.scores?.trend||0)*100)}%</b></div>
                      <div>ML: <b>{Math.round((ev.payload?.scores?.ml||0)*100)}%</b></div>
                      <div>News Bias: <b>{(ev.payload?.scores?.news_bias ?? 0).toFixed(3)}</b></div>
                      <div>Telegram Bias: <b>{(ev.payload?.scores?.telegram_bias ?? 0).toFixed(3)}</b></div>
                      {ev.payload?.gate && (
                        <div className="col-span-2">
                          Gate: <span className={`px-2 py-0.5 rounded-xl border ${ev.payload.gate.reason ? 'text-red-600 border-red-300' : 'text-emerald-700 border-emerald-300'}`}>
                            mode={ev.payload.gate.mode} {ev.payload.gate.reason ? `blocked(${ev.payload.gate.reason})` : 'ok'}
                          </span>
                        </div>
                      )}
                      {ev.payload?.telegram?.pulse && (
                        <div className="col-span-2">
                          Pulse: <b>x{Number(ev.payload.telegram.pulse.factor||1).toFixed(2)}</b>
                          {ev.payload.telegram.pulse.side && <> <span className="mx-1">•</span> {ev.payload.telegram.pulse.side}</>}
                          {typeof ev.payload.telegram.pulse.age_min === 'number' && <> <span className="mx-1">•</span> {Math.round(ev.payload.telegram.pulse.age_min)}m</>}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="p-4 bg-zinc-900 rounded">
          <OnChain />
        </div>
        <div className="p-4 bg-zinc-900 rounded">
          <MEVFeed />
        </div>
        <div className="p-4 bg-zinc-900 rounded">
          <NFTSniper />
        </div>
        <div className="p-4 bg-zinc-900 rounded">
          <Trades />
        </div>
        <div className="p-4 bg-zinc-900 rounded">
          <Signals />
        </div>
        <div className="p-4 bg-zinc-900 rounded col-span-1 md:col-span-2">
          <SignalsTimeline />
        </div>
        <DEXQuoteCard />
        <NFTFloorCard />
        <L2YieldsCard />
        <DEXSparkline />
        <L2YieldsBar />
      </div>
    </div>
  )
}


