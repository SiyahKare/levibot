export type EventRec = {
  ts?: number;
  _ts?: number;
  event_type: string;
  symbol?: string;
  payload?: Record<string, unknown>;
  trace_id?: string;
};

export function getTs(rec: EventRec): number {
  if (typeof rec.ts === "number") return rec.ts;
  if (typeof rec._ts === "number") return rec._ts;
  return Date.now();
}

export type TelegramSignal = {
  ts: string;
  chat_title: string;
  symbol: string;
  side: string;
  confidence: number;
  trace_id: string;
};

export type TelegramSignalsResponse = {
  ok: boolean;
  signals: TelegramSignal[];
};

export type TelegramAiBrainAskPayload = {
  question: string;
  recent_signals?: Array<{
    chat_title: string;
    symbol: string;
    side: string;
    confidence?: number;
    ts: string;
  }>;
  metrics?: Record<string, unknown>;
};

export type TelegramAiBrainAskResponse = {
  ok: boolean;
  answer: string;
  reasoning?: string;
  recommendations?: string[];
  metadata?: Record<string, unknown>;
};






