/**
 * SSE Status Indicator
 * Shows live connection status to SSE stream with auto-reconnect
 */
import { useEffect, useRef, useState } from "react";

export function SSEStatus() {
  const [live, setLive] = useState(false);
  const backoffRef = useRef(1000); // Start with 1s
  const esRef = useRef<EventSource | null>(null);
  const timerRef = useRef<number | undefined>(undefined);

  useEffect(() => {
    const connect = () => {
      // Close existing connection
      if (esRef.current) {
        esRef.current.close();
      }

      // Create new connection
      // Note: Using /stream/engines as /stream/ticks is not implemented yet
      const es = new EventSource("http://localhost:8000/stream/engines");
      esRef.current = es;

      es.onopen = () => {
        setLive(true);
        backoffRef.current = 1000; // Reset backoff on successful connect
      };

      es.onmessage = () => {
        setLive(true);
      };

      es.onerror = () => {
        setLive(false);
        es.close();

        // Schedule reconnect with exponential backoff (max 30s)
        const delay = Math.min(backoffRef.current, 30000);
        window.clearTimeout(timerRef.current);
        timerRef.current = window.setTimeout(connect, delay);

        // Increase backoff for next attempt
        backoffRef.current = Math.min(delay * 2, 30000);
      };
    };

    // Initial connection
    connect();

    // Cleanup
    return () => {
      window.clearTimeout(timerRef.current);
      if (esRef.current) {
        esRef.current.close();
      }
    };
  }, []);

  return (
    <div className="flex items-center gap-2">
      <span
        className={`h-2 w-2 rounded-full ${
          live ? "bg-green-500 animate-pulse" : "bg-zinc-400 animate-ping"
        }`}
      />
      <span className="text-sm font-medium">
        {live ? "LIVE" : "RECONNECTING..."}
      </span>
    </div>
  );
}
