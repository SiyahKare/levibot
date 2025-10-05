export async function fetchClosed(limit = 200): Promise<any[]> {
  const url = `/events?event_type=POSITION_CLOSED&limit=${limit}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`events fetch failed: ${res.status}`);
  return await res.json();
}

export async function fetchEvents(types: string, limit = 500): Promise<any[]> {
  const url = `/events?event_type=${encodeURIComponent(types)}&limit=${limit}`;
  const r = await fetch(url);
  if (!r.ok) throw new Error(`fetch ${types} failed`);
  return await r.json();
}

export async function getRiskPolicy() {
  const r = await fetch("/risk/policy");
  if (!r.ok) throw new Error("policy get failed");
  return r.json();
}

export async function setRiskPolicy(name: string, apiKey?: string) {
  const headers: Record<string,string> = {"Content-Type":"application/json"};
  if (apiKey) headers["X-API-Key"] = apiKey;
  const r = await fetch("/risk/policy", { method:"PUT", headers, body: JSON.stringify({name}) });
  if (!r.ok) throw new Error("policy put failed");
  return r.json();
}

export async function getDexQuote(params: {sell:string; buy:string; amount:number; chain?:string}) {
  const q = new URLSearchParams({ sell: params.sell, buy: params.buy, amount: String(params.amount), ...(params.chain?{chain:params.chain}:{}) });
  const r = await fetch(`/dex/quote?${q.toString()}`); if (!r.ok) throw new Error("dex quote failed"); return r.json();
}

export async function getNftFloor(collection: string) {
  const r = await fetch(`/nft/floor?collection=${encodeURIComponent(collection)}`); if (!r.ok) throw new Error("nft floor failed"); return r.json();
}

export async function getNftSnipePlan(collection: string, budget: number, discountPct: number) {
  const q = new URLSearchParams({ collection, budget_usd: String(budget), discount_pct: String(discountPct) });
  const r = await fetch(`/nft/snipe/plan?${q.toString()}`); if (!r.ok) throw new Error("nft snipe failed"); return r.json();
}

export async function getL2Yields() {
  const r = await fetch(`/l2/yields`); if (!r.ok) throw new Error("l2 yields failed"); return r.json();
}

export async function getDexQuoteSeries(sell="ETH", buy="USDC", points=20){
  // basit client-side timeseries: ardışık 20 quote çekip timestamp'li dön
  const out:{t:number; p:number}[]=[]
  for(let i=0;i<points;i++){
    const r=await fetch(`/dex/quote?sell=${sell}&buy=${buy}&amount=0.1`);
    const j=await r.json(); out.push({t:Date.now(), p:j.price||null});
    await new Promise(r=>setTimeout(r,150)); // kısa bekleme (demo için)
  }
  return out;
}

