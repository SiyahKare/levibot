/**
 * Backtest Runner Page
 * Run backtests and view historical reports
 * Sprint-10 Epic-D Integration
 */
import { api } from "@/lib/api";
import { useEffect, useState } from "react";
import { toast } from "sonner";

type BacktestReport = {
  id: string;
  symbol: string;
  window: string;
  created_at: string;
  metrics?: {
    sharpe?: number;
    sortino?: number;
    max_drawdown?: number;
    win_rate?: number;
    ann_return?: number;
    total_trades?: number;
  };
  links?: {
    json?: string;
    markdown?: string;
  };
};

export default function BacktestRunner() {
  const [reports, setReports] = useState<BacktestReport[]>([]);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);

  // Form state
  const [form, setForm] = useState({
    symbol: "BTC/USDT",
    days: 30,
    fee_bps: 5,
    slippage_bps: 5,
    max_pos: 1.0,
  });

  const loadReports = async () => {
    setLoading(true);
    try {
      const list = await api.backtest.list();
      setReports(list);
    } catch (error: any) {
      toast.error(`Failed to load reports: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, []);

  const handleRun = async () => {
    if (!form.symbol || form.days < 1) {
      toast.error("Invalid parameters");
      return;
    }

    setRunning(true);
    try {
      await api.backtest.run(form);
      toast.success("Backtest started! Refresh to see results.");
      await loadReports();
    } catch (error: any) {
      toast.error(`Backtest failed: ${error.message}`);
    } finally {
      setRunning(false);
    }
  };

  return (
    <main className="p-6 space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
          Backtest Runner
        </h1>
        <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-1">
          Simulate strategies on historical data with vectorized execution
        </p>
      </header>

      {/* Run Form */}
      <section className="p-6 border border-zinc-200 dark:border-zinc-800 rounded-2xl bg-white dark:bg-zinc-900 space-y-4">
        <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
          New Backtest
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
              Symbol
            </label>
            <input
              type="text"
              value={form.symbol}
              onChange={(e) => setForm({ ...form, symbol: e.target.value })}
              placeholder="BTC/USDT"
              className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
              Days
            </label>
            <input
              type="number"
              value={form.days}
              onChange={(e) => setForm({ ...form, days: +e.target.value })}
              min={1}
              max={365}
              className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
              Fee (bps)
            </label>
            <input
              type="number"
              value={form.fee_bps}
              onChange={(e) => setForm({ ...form, fee_bps: +e.target.value })}
              min={0}
              max={100}
              step={1}
              className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
              Slippage (bps)
            </label>
            <input
              type="number"
              value={form.slippage_bps}
              onChange={(e) =>
                setForm({ ...form, slippage_bps: +e.target.value })
              }
              min={0}
              max={100}
              step={1}
              className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
              Max Position
            </label>
            <input
              type="number"
              value={form.max_pos}
              onChange={(e) => setForm({ ...form, max_pos: +e.target.value })}
              min={0.1}
              max={2.0}
              step={0.1}
              className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 focus:border-transparent"
            />
          </div>
        </div>

        <button
          disabled={running}
          onClick={handleRun}
          className="px-6 py-2.5 rounded-lg text-sm font-medium bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {running ? "Running..." : "Run Backtest"}
        </button>
      </section>

      {/* Reports List */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
            Recent Reports
          </h2>
          <button
            disabled={loading}
            onClick={loadReports}
            className="px-3 py-1.5 rounded-lg text-xs font-medium bg-zinc-200 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-300 dark:hover:bg-zinc-700 disabled:opacity-50 transition-colors"
          >
            Refresh
          </button>
        </div>

        {loading ? (
          <div className="animate-pulse space-y-3">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-24 bg-zinc-200 dark:bg-zinc-800 rounded-lg"
              ></div>
            ))}
          </div>
        ) : reports.length === 0 ? (
          <div className="p-12 text-center border border-dashed border-zinc-300 dark:border-zinc-700 rounded-2xl">
            <div className="text-4xl mb-4">📊</div>
            <h3 className="text-lg font-medium text-zinc-900 dark:text-zinc-100 mb-2">
              No reports yet
            </h3>
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              Run your first backtest to see results here
            </p>
          </div>
        ) : (
          <div className="divide-y divide-zinc-200 dark:divide-zinc-800 border border-zinc-200 dark:border-zinc-800 rounded-lg">
            {reports.map((report) => (
              <div
                key={report.id}
                className="p-4 hover:bg-zinc-50 dark:hover:bg-zinc-900/50 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-medium text-zinc-900 dark:text-zinc-100">
                        {report.symbol}
                      </h3>
                      <span className="px-2 py-0.5 rounded text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300">
                        {report.window}
                      </span>
                      <span className="text-xs text-zinc-500 dark:text-zinc-400">
                        {new Date(report.created_at).toLocaleString()}
                      </span>
                    </div>

                    {report.metrics && (
                      <div className="grid grid-cols-2 md:grid-cols-6 gap-4 text-sm">
                        <div>
                          <div className="text-xs text-zinc-500 dark:text-zinc-400">
                            Sharpe
                          </div>
                          <div className="font-semibold text-zinc-900 dark:text-zinc-100">
                            {report.metrics.sharpe?.toFixed(2) ?? "-"}
                          </div>
                        </div>
                        <div>
                          <div className="text-xs text-zinc-500 dark:text-zinc-400">
                            Sortino
                          </div>
                          <div className="font-semibold text-zinc-900 dark:text-zinc-100">
                            {report.metrics.sortino?.toFixed(2) ?? "-"}
                          </div>
                        </div>
                        <div>
                          <div className="text-xs text-zinc-500 dark:text-zinc-400">
                            Max DD
                          </div>
                          <div
                            className={`font-semibold ${
                              (report.metrics.max_drawdown ?? 0) < -0.1
                                ? "text-rose-600 dark:text-rose-400"
                                : "text-zinc-900 dark:text-zinc-100"
                            }`}
                          >
                            {((report.metrics.max_drawdown ?? 0) * 100).toFixed(
                              1
                            )}
                            %
                          </div>
                        </div>
                        <div>
                          <div className="text-xs text-zinc-500 dark:text-zinc-400">
                            Win Rate
                          </div>
                          <div className="font-semibold text-zinc-900 dark:text-zinc-100">
                            {((report.metrics.win_rate ?? 0) * 100).toFixed(1)}%
                          </div>
                        </div>
                        <div>
                          <div className="text-xs text-zinc-500 dark:text-zinc-400">
                            Ann. Return
                          </div>
                          <div
                            className={`font-semibold ${
                              (report.metrics.ann_return ?? 0) > 0
                                ? "text-emerald-600 dark:text-emerald-400"
                                : "text-rose-600 dark:text-rose-400"
                            }`}
                          >
                            {((report.metrics.ann_return ?? 0) * 100).toFixed(
                              1
                            )}
                            %
                          </div>
                        </div>
                        <div>
                          <div className="text-xs text-zinc-500 dark:text-zinc-400">
                            Trades
                          </div>
                          <div className="font-semibold text-zinc-900 dark:text-zinc-100">
                            {report.metrics.total_trades ?? "-"}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="flex gap-2 ml-4">
                    {report.links?.markdown && (
                      <a
                        href={report.links.markdown}
                        target="_blank"
                        rel="noreferrer"
                        className="px-3 py-1.5 rounded-lg text-xs font-medium bg-zinc-200 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-300 dark:hover:bg-zinc-700 transition-colors"
                      >
                        Report
                      </a>
                    )}
                    {report.links?.json && (
                      <a
                        href={report.links.json}
                        target="_blank"
                        rel="noreferrer"
                        className="px-3 py-1.5 rounded-lg text-xs font-medium bg-zinc-200 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-300 dark:hover:bg-zinc-700 transition-colors"
                      >
                        JSON
                      </a>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}

