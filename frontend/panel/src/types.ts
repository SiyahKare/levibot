export type EventRec = {
  ts?: number; // optional; backend may use different ts key (_ts, etc.)
  _ts?: number;
  event_type: string;
  symbol?: string;
  payload?: Record<string, any>;
  trace_id?: string;
};

export function getTs(rec: EventRec): number {
  return typeof rec.ts === "number" ? rec.ts : typeof rec._ts === "number" ? rec._ts : Date.now();
}



