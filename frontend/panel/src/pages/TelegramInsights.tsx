import { useEffect, useState } from "react";

type Group = { chat: string; reputation: number; signals: number };

export default function TelegramInsights() {
  const [rows, setRows] = useState<Group[]>([]);
  useEffect(() => {
    fetch("http://localhost:8000/telegram/reputation")
      .then((r) => r.json())
      .then((d) => setRows(d.groups || []));
  }, []);
  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold mb-3">Telegram Group Reputation (14d)</h2>
      <div className="overflow-x-auto rounded-2xl border">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-zinc-500">
              <th className="py-2 px-3">Group</th>
              <th>Reputation</th>
              <th>Signals</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((g, i) => (
              <tr key={i} className="border-t">
                <td className="py-2 px-3">{g.chat}</td>
                <td>{Math.round((g.reputation || 0) * 100)}%</td>
                <td>{g.signals}</td>
              </tr>
            ))}
            {!rows.length && (
              <tr>
                <td className="py-3 px-3 text-zinc-500" colSpan={3}>
                  No data
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
















