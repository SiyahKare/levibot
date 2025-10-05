import { useState, useEffect } from "react";
import { getAlertsHistory, triggerTestAlert } from "../api";

interface Alert {
  timestamp: string;
  title: string;
  summary: string;
  severity: string;
  source: string;
  labels?: Record<string, string>;
}

const SEVERITY_COLORS: Record<string, string> = {
  info: "bg-blue-100 text-blue-800",
  low: "bg-gray-100 text-gray-800",
  medium: "bg-yellow-100 text-yellow-800",
  high: "bg-orange-100 text-orange-800",
  critical: "bg-red-100 text-red-800",
};

export default function Alerts() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  
  // Filters
  const [severityFilter, setSeverityFilter] = useState("");
  const [sourceFilter, setSourceFilter] = useState("");
  const [daysFilter, setDaysFilter] = useState(7);
  const [searchFilter, setSearchFilter] = useState("");
  
  // Pagination
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(25);
  
  // Unread badge
  const [unreadCount, setUnreadCount] = useState(0);
  const [lastViewTime, setLastViewTime] = useState(Date.now());
  
  // Test alert button (hidden by default)
  const showTestButton = import.meta.env.VITE_SHOW_TEST_ALERT === "true";

  const fetchAlerts = async () => {
    try {
      const data = await getAlertsHistory({
        severity: severityFilter || undefined,
        source: sourceFilter || undefined,
        days: daysFilter,
        limit: 300,
      });
      setAlerts(data.alerts || []);
      
      // Count unread (alerts newer than last view)
      const unread = (data.alerts || []).filter(
        (a: Alert) => new Date(a.timestamp).getTime() > lastViewTime
      ).length;
      setUnreadCount(unread);
      
      setError("");
    } catch (err: any) {
      setError(err.message || "Failed to fetch alerts");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
    // Poll every 5 seconds
    const interval = setInterval(fetchAlerts, 5000);
    return () => clearInterval(interval);
  }, [severityFilter, sourceFilter, daysFilter]);

  // Reset unread when tab is focused
  useEffect(() => {
    const handleFocus = () => {
      setLastViewTime(Date.now());
      setUnreadCount(0);
    };
    window.addEventListener("focus", handleFocus);
    return () => window.removeEventListener("focus", handleFocus);
  }, []);

  const handleTestAlert = async () => {
    try {
      await triggerTestAlert({ severity: "info", title: "Test Alert", summary: "Panel test" });
      setTimeout(fetchAlerts, 1000); // Refresh after 1s
    } catch (err: any) {
      alert(`Test alert failed: ${err.message}`);
    }
  };

  // Apply search filter
  const filtered = alerts.filter((a) => {
    if (!searchFilter) return true;
    const search = searchFilter.toLowerCase();
    return (
      a.title?.toLowerCase().includes(search) ||
      a.summary?.toLowerCase().includes(search) ||
      a.source?.toLowerCase().includes(search)
    );
  });

  // Pagination
  const totalPages = Math.ceil(filtered.length / perPage);
  const startIdx = (page - 1) * perPage;
  const paginated = filtered.slice(startIdx, startIdx + perPage);

  if (loading && alerts.length === 0) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-4">Alerts</h1>
        <p className="text-gray-600">Loading alerts...</p>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold">Alerts</h1>
          {unreadCount > 0 && (
            <span className="px-2 py-1 text-xs font-semibold bg-red-500 text-white rounded-full">
              {unreadCount} new
            </span>
          )}
        </div>
        {showTestButton && (
          <button
            onClick={handleTestAlert}
            className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Test Alert
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Severity</label>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="border rounded px-3 py-1.5 text-sm"
          >
            <option value="">All</option>
            <option value="info">Info</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Source</label>
          <select
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value)}
            className="border rounded px-3 py-1.5 text-sm"
          >
            <option value="">All</option>
            <option value="auto">Auto</option>
            <option value="manual">Manual</option>
            <option value="signals">Signals</option>
            <option value="risk">Risk</option>
            <option value="exec">Exec</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Days</label>
          <select
            value={daysFilter}
            onChange={(e) => setDaysFilter(Number(e.target.value))}
            className="border rounded px-3 py-1.5 text-sm"
          >
            <option value={1}>1 day</option>
            <option value={3}>3 days</option>
            <option value={7}>7 days</option>
            <option value={30}>30 days</option>
          </select>
        </div>

        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-1">Search</label>
          <input
            type="text"
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            placeholder="Search title, summary, source..."
            className="border rounded px-3 py-1.5 text-sm w-full max-w-md"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Per Page</label>
          <select
            value={perPage}
            onChange={(e) => {
              setPerPage(Number(e.target.value));
              setPage(1);
            }}
            className="border rounded px-3 py-1.5 text-sm"
          >
            <option value={25}>25</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-100 text-red-800 rounded">
          Error: {error}
        </div>
      )}

      {/* Alerts Table */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        {paginated.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            No alerts found. Try adjusting your filters.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Timestamp
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Title
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Severity
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Source
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Details
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {paginated.map((alert, idx) => {
                  const isNew = new Date(alert.timestamp).getTime() > lastViewTime;
                  return (
                    <tr key={idx} className={isNew ? "bg-blue-50" : ""}>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                        {new Date(alert.timestamp).toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900 font-medium">
                        {alert.title}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 text-xs font-semibold rounded ${
                            SEVERITY_COLORS[alert.severity] || "bg-gray-100 text-gray-800"
                          }`}
                        >
                          {alert.severity}
                        </span>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                        {alert.source}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        <div className="max-w-md truncate">{alert.summary}</div>
                        {alert.labels && Object.keys(alert.labels).length > 0 && (
                          <div className="mt-1 flex flex-wrap gap-1">
                            {Object.entries(alert.labels).map(([k, v]) => (
                              <span
                                key={k}
                                className="px-1.5 py-0.5 text-xs bg-gray-100 text-gray-700 rounded"
                              >
                                {k}: {v}
                              </span>
                            ))}
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="mt-4 flex items-center justify-between">
          <div className="text-sm text-gray-600">
            Showing {startIdx + 1}–{Math.min(startIdx + perPage, filtered.length)} of{" "}
            {filtered.length} alerts
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1 text-sm border rounded disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <span className="px-3 py-1 text-sm">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-3 py-1 text-sm border rounded disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
