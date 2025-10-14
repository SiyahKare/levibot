import { useEffect, useMemo, useState } from "react";
import { askTelegramBrain } from "../api";
import type {
  TelegramAiBrainAskPayload,
  TelegramAiBrainAskResponse,
} from "../types";

type Group = { chat: string; reputation: number; signals: number };

type RankedGroup = Group & {
  rank: number;
};

const TOP_SIGNAL_LIMIT = 8;

export default function TelegramInsights() {
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(true);
  const [question, setQuestion] = useState(
    "Which Telegram channels look most trustworthy right now?"
  );
  const [aiAnswer, setAiAnswer] = useState<TelegramAiBrainAskResponse | null>(
    null
  );
  const [thinking, setThinking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch("/telegram/reputation");
        const data = await res.json();
        setGroups(data.groups || []);
      } catch (err) {
        console.error("Failed to load reputation", err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const rankedGroups: RankedGroup[] = useMemo(() => {
    const sorted = [...groups].sort((a, b) => b.reputation - a.reputation);
    return sorted.map((g, idx) => ({ ...g, rank: idx + 1 }));
  }, [groups]);

  const recentSignalsForAi = useMemo(
    () =>
      rankedGroups.slice(0, TOP_SIGNAL_LIMIT).map((g) => ({
        chat_title: g.chat,
        symbol: "N/A",
        side: g.reputation >= 0.6 ? "buy" : "neutral",
        confidence: g.reputation,
        ts: new Date().toISOString(),
      })),
    [rankedGroups]
  );

  const askAi = async () => {
    setThinking(true);
    setError(null);
    try {
      const payload: TelegramAiBrainAskPayload = {
        question,
        recent_signals: recentSignalsForAi,
        metrics: {
          group_count: groups.length,
          top3_avg_reputation:
            rankedGroups
              .slice(0, 3)
              .reduce((acc, cur) => acc + cur.reputation, 0) /
            Math.max(1, Math.min(3, rankedGroups.length)),
        },
      };
      const ai = await askTelegramBrain(payload);
      setAiAnswer(ai);
    } catch (err: any) {
      setError(err?.message || "AI request failed");
    } finally {
      setThinking(false);
    }
  };

  return (
    <div className="p-4 space-y-6">
      <section className="bg-zinc-900 border border-zinc-800 rounded-2xl p-4">
        <header className="flex items-start justify-between gap-4 mb-4">
          <div>
            <h2 className="text-lg font-semibold">
              Telegram Group Reputation (last 14 days)
            </h2>
            <p className="text-sm text-zinc-400">
              Reputation is derived from signal accuracy and staleness metrics.
            </p>
          </div>
          <button
            onClick={() => window.location.reload()}
            className="px-3 py-1 rounded-lg border border-zinc-600 text-sm hover:bg-zinc-800"
          >
            Refresh
          </button>
        </header>
        <div className="overflow-x-auto rounded-2xl border border-zinc-800">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-zinc-500">
                <th className="py-2 px-3">Rank</th>
                <th>Group</th>
                <th>Reputation</th>
                <th>Signals</th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr>
                  <td colSpan={4} className="py-6 text-center text-zinc-500">
                    Loading...
                  </td>
                </tr>
              )}
              {!loading && rankedGroups.length === 0 && (
                <tr>
                  <td colSpan={4} className="py-6 text-center text-zinc-500">
                    No data
                  </td>
                </tr>
              )}
              {rankedGroups.map((g) => (
                <tr key={g.chat} className="border-t border-zinc-800">
                  <td className="py-2 px-3">#{g.rank}</td>
                  <td>{g.chat}</td>
                  <td>{Math.round((g.reputation || 0) * 100)}%</td>
                  <td>{g.signals}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="bg-gradient-to-br from-zinc-900 to-zinc-800 border border-zinc-700 rounded-2xl p-4 space-y-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          🤖 Telegram AI Insights
        </h3>
        <div className="space-y-3">
          <label className="text-sm text-zinc-400 block">
            Ask GPT about Telegram signal quality:
          </label>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            className="w-full bg-zinc-900 border border-zinc-700 rounded-xl p-3 text-sm focus:outline-none focus:ring"
            rows={2}
          />
          <button
            onClick={askAi}
            disabled={thinking}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-xl text-sm font-semibold"
          >
            {thinking ? "Thinking..." : "Ask AI"}
          </button>
          {error && <p className="text-sm text-red-400">{error}</p>}
        </div>

        {aiAnswer && (
          <div className="bg-zinc-900/60 border border-zinc-700 rounded-xl p-4 space-y-3">
            <div>
              <div className="text-xs uppercase text-zinc-500">Answer</div>
              <p className="text-sm text-zinc-100 whitespace-pre-line">
                {aiAnswer.answer}
              </p>
            </div>
            {aiAnswer.reasoning && (
              <div>
                <div className="text-xs uppercase text-zinc-500">Reasoning</div>
                <p className="text-sm text-zinc-300 whitespace-pre-line">
                  {aiAnswer.reasoning}
                </p>
              </div>
            )}
            {aiAnswer.recommendations?.length && (
              <div>
                <div className="text-xs uppercase text-zinc-500">
                  Recommendations
                </div>
                <ul className="list-disc list-inside text-sm text-zinc-300 space-y-1">
                  {aiAnswer.recommendations.map((rec, idx) => (
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
