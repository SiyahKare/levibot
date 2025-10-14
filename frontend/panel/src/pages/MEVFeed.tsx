import { useEffect, useState } from "react";

type Ev = { ts: string; event_type: string; payload: any };

export default function MEVFeed() {
  const [risk, setRisk] = useState<Ev[]>([]);
  const [arb, setArb] = useState<Ev[]>([]);
  const [liq, setLiq] = useState<Ev[]>([]);
  const load = async () => {
    const base = "/events?limit=200&event_type=";
    const [r1, r2, r3] = await Promise.all([
      fetch(base + "MEV_RISK").then((r) => r.json()),
      fetch(base + "MEV_ARB_OPP").then((r) => r.json()),
      fetch(base + "MEV_LIQ_OPP").then((r) => r.json()),
    ]);
    setRisk(r1);
    setArb(r2);
    setLiq(r3);
  };
  useEffect(() => {
    load();
    const id = setInterval(load, 6000);
    return () => clearInterval(id);
  }, []);
  return (
    <div className="space-y-6">
      <section className="p-4">
        <h2 className="text-lg font-semibold mb-3">Sandwich Hazard</h2>
        <div className="overflow-x-auto rounded-2xl border">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-zinc-500">
                <th className="py-2 px-3">Time</th>
                <th>Symbol</th>
                <th>Est bps</th>
              </tr>
            </thead>
            <tbody>
              {risk.map((r, i) => (
                <tr key={i} className="border-t">
                  <td className="py-2 px-3">
                    {new Date(r.ts).toLocaleTimeString()}
                  </td>
                  <td>{r.payload?.symbol}</td>
                  <td>
                    <span className="px-2 py-0.5 bg-amber-900/40 border border-amber-500 text-amber-200 rounded">
                      {r.payload?.est_bps}
                    </span>
                  </td>
                </tr>
              ))}
              {!risk.length && (
                <tr>
                  <td className="py-3 px-3 text-zinc-500" colSpan={3}>
                    No risk
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
      <section className="p-4">
        <h2 className="text-lg font-semibold mb-3">Arbitrage Opportunities</h2>
        <div className="overflow-x-auto rounded-2xl border">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-zinc-500">
                <th className="py-2 px-3">Time</th>
                <th>Symbol</th>
                <th>Edge (bps)</th>
                <th>Route</th>
              </tr>
            </thead>
            <tbody>
              {arb.map((r, i) => (
                <tr key={i} className="border-t">
                  <td className="py-2 px-3">
                    {new Date(r.ts).toLocaleTimeString()}
                  </td>
                  <td>{r.payload?.symbol}</td>
                  <td>{r.payload?.edge_bps}</td>
                  <td>
                    <code className="text-xs">
                      {JSON.stringify(r.payload?.route || [])}
                    </code>
                  </td>
                </tr>
              ))}
              {!arb.length && (
                <tr>
                  <td className="py-3 px-3 text-zinc-500" colSpan={4}>
                    No opps
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
      <section className="p-4">
        <h2 className="text-lg font-semibold mb-3">Liquidation Windows</h2>
        <div className="overflow-x-auto rounded-2xl border">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-zinc-500">
                <th className="py-2 px-3">Time</th>
                <th>Protocol</th>
                <th>Market</th>
                <th>Account</th>
                <th>Est Profit</th>
              </tr>
            </thead>
            <tbody>
              {liq.map((r, i) => (
                <tr key={i} className="border-t">
                  <td className="py-2 px-3">
                    {new Date(r.ts).toLocaleTimeString()}
                  </td>
                  <td>{r.payload?.protocol}</td>
                  <td>{r.payload?.market}</td>
                  <td>{r.payload?.account}</td>
                  <td>${r.payload?.est_profit_usd}</td>
                </tr>
              ))}
              {!liq.length && (
                <tr>
                  <td className="py-3 px-3 text-zinc-500" colSpan={5}>
                    No windows
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
