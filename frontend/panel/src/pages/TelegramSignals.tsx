import { useEffect, useMemo, useState } from "react";
import { askTelegramBrain } from "../api";
import type { TelegramAiBrainAskResponse } from "../types";

type TSignal = {
  ts: string;
  chat_title: string;
  symbol: string;
  side: string;
  confidence: number;
  trace_id: string;
};

export default function TelegramSignals() {
  const [rows, setRows] = useState<TSignal[]>([]);
  const [gate, setGate] = useState<{ max_age_min: number }>({
    max_age_min: 120,
  });
  const [question, setQuestion] = useState(
    "Is there anything actionable in the latest Telegram feed?"
  );
  const [aiReply, setAiReply] = useState<TelegramAiBrainAskResponse | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const [thinking, setThinking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const r = await fetch("/telegram/signals");
        setRows(await r.json());
      } catch (err) {
        console.error("Failed to load telegram signals", err);
      } finally {
        setLoading(false);
      }
    };

    load();
    const id = setInterval(load, 8000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    fetch("/config")
      .then((r) => r.json())
      .then((cfg) => {
        const g = (cfg as any)?.features?.telegram?.evaluation?.gate || {};
        setGate({ max_age_min: g.max_age_min ?? 120 });
      })
      .catch((err) => console.error(err));
  }, []);

  const recentSignals = useMemo(
    () =>
      rows.slice(0, 12).map((r) => ({
        chat_title: r.chat_title,
        symbol: r.symbol,
        side: r.side,
        confidence: r.confidence,
        ts: r.ts,
      })),
    [rows]
  );

  const askAi = async () => {
    setThinking(true);
    setError(null);
    try {
      const response = await askTelegramBrain({
        question,
        recent_signals: recentSignals,
        metrics: {
          fresh_ratio:
            rows.length === 0
              ? 0
              : rows.filter(
                  (r) =>
                    (Date.now() - new Date(r.ts).getTime()) / 60000 <=
                    gate.max_age_min
                ).length / rows.length,
          signal_count: rows.length,
        },
      });
      setAiReply(response);
    } catch (err: any) {
      setError(err?.message || "Failed to ask AI");
    } finally {
      setThinking(false);
    }
  };

  return (
    <div className="p-4 space-y-6">
      <section className="bg-zinc-900 rounded-2xl border border-zinc-800">
        <header className="flex items-start justify-between p-4 border-b border-zinc-800">
          <div>
            <h2 className="text-lg font-semibold">Telegram Signals</h2>
            <p className="text-sm text-zinc-400">
              Live feed of Telegram strategy signals with freshness gate check.
            </p>
          </div>
          <div className="text-xs text-zinc-500">
            Gate max age: {gate.max_age_min} min
          </div>
        </header>

        <div className="overflow-x-auto max-h-[480px] rounded-b-2xl">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-zinc-500">
                <th className="py-2 px-3">Time</th>
                <th>Group</th>
                <th>Symbol</th>
                <th>Side</th>
                <th>Conf.</th>
                <th>Status</th>
                <th>Trace</th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr>
                  <td colSpan={7} className="py-6 text-center text-zinc-500">
                    Loading...
                  </td>
                </tr>
              )}
              {!loading &&
                rows.map((r, i) => {
                  const ageMin =
                    (Date.now() - new Date(r.ts).getTime()) / 60000;
                  const fresh = ageMin <= gate.max_age_min;
                  return (
                    <tr
                      key={`${r.trace_id}-${i}`}
                      className="border-t border-zinc-800"
                    >
                      <td className="py-2 px-3">
                        {new Date(r.ts).toLocaleString()}
                      </td>
                      <td>{r.chat_title}</td>
                      <td className="font-medium">{r.symbol}</td>
                      <td>{r.side}</td>
                      <td>{Math.round((r.confidence || 0) * 100)}%</td>
                      <td>
                        <span
                          className={`px-2 py-0.5 rounded-xl border ${
                            fresh
                              ? "text-emerald-500 border-emerald-400/50"
                              : "text-zinc-500 border-zinc-400/40"
                          }`}
                        >
                          {fresh ? "Fresh" : "Stale"}
                        </span>
                      </td>
                      <td>
                        <button
                          className="px-2 py-1 rounded-lg border border-zinc-700 hover:bg-zinc-800"
                          onClick={() =>
                            window.dispatchEvent(
                              new CustomEvent("open-trace", {
                                detail: r.trace_id,
                              })
                            )
                          }
                        >
                          Trace
                        </button>
                      </td>
                    </tr>
                  );
                })}
              {!loading && rows.length === 0 && (
                <tr>
                  <td colSpan={7} className="py-6 text-center text-zinc-500">
                    No signals yet
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="bg-zinc-900 rounded-2xl border border-zinc-800 p-4 space-y-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          🧠 Quick AI Summary
        </h3>
        <div className="space-y-3">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            className="w-full bg-zinc-900 border border-zinc-700 rounded-xl p-3 text-sm focus:outline-none focus:ring"
            rows={2}
          />
          <button
            disabled={thinking}
            onClick={askAi}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-xl text-sm font-semibold"
          >
            {thinking ? "Thinking..." : "Ask AI"}
          </button>
          {error && <p className="text-sm text-red-400">{error}</p>}
        </div>

        {aiReply && (
          <div className="bg-zinc-900/70 border border-zinc-700 rounded-xl p-4 space-y-3">
            <div>
              <div className="text-xs uppercase text-zinc-500">Answer</div>
              <p className="text-sm text-zinc-100 whitespace-pre-line">
                {aiReply.answer}
              </p>
            </div>
            {aiReply.reasoning && (
              <div>
                <div className="text-xs uppercase text-zinc-500">Reasoning</div>
                <p className="text-sm text-zinc-300 whitespace-pre-line">
                  {aiReply.reasoning}
                </p>
              </div>
            )}
            {aiReply.recommendations?.length && (
              <div>
                <div className="text-xs uppercase text-zinc-500">
                  Recommendations
                </div>
                <ul className="list-disc list-inside text-sm text-zinc-300 space-y-1">
                  {aiReply.recommendations.map((rec, idx) => (
                    <li key={idx}>{rec}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
