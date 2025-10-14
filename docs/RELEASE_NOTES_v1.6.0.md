# 🚀 LeviBot v1.6.0 — *Pulse* (Event Intelligence + Real-time)

**Release Date:** October 6, 2025  
**Codename:** *Pulse*  

## 🎯 Öne Çıkanlar

* **PR-40 — Smart Event Filters:** `/events` için `event_type`, `symbol`, `trace_id`, `since_iso`, `q` filtreleri.
* **PR-41 — Event Timeline UI:** Recharts scatter timeline, 15+ event tipi renk kodlu, quick date (24h/7d/30d), trace highlight, 10s auto-refresh.
* **PR-42 — Real-time WS Stream:** `/ws/events` WebSocket + hafif in-memory pub/sub, auto-reconnect'li frontend client, Prometheus WS metrikleri.

---

## 🛠 Detaylar

### Backend

**Smart Event Filters (PR-40)**
- `event_type`: CSV list filter (e.g., `SIGNAL_SCORED,POSITION_CLOSED`)
- `symbol`: Exact match filter (e.g., `BTCUSDT`)
- `trace_id`: Debug filter for tracing event chains
- `since_iso`: Date range filter (ISO 8601)
- `q`: Full-text search in event payload
- `limit`: 1-1000 (default 200)
- `days`: 1-7 (default 1)

**WebSocket Event Stream (PR-42)**
- `backend/src/infra/ws_bus.py`: In-memory pub/sub system
  - 2048 message buffer per subscriber
  - Backpressure handling (drop on queue full)
  - Non-blocking fanout
- `/ws/events` endpoint with smart filters
  - Real-time event streaming
  - Filter support: `event_type`, `symbol`, `q`
  - Hello frame for connection health
- Event logger integration
  - `log_event()` publishes to EventBus
  - Non-blocking `asyncio.create_task()`
  - Graceful fallback when event loop unavailable

**Prometheus Metrics**
- `levibot_ws_conns`: Active WebSocket connections (Gauge)
- `levibot_ws_msgs_out_total`: Messages sent over WebSocket (Counter)
- `levibot_ws_msgs_drop_total`: Messages dropped due to backpressure (Counter)

### Frontend

**Event Timeline UI (PR-41)**
- **Recharts scatter plot** visualization
- **15+ event types** with color coding
- **Quick filters**: 24h / 7d / 30d buttons
- **Smart filters**: Event type multiselect, symbol input, text search
- **Trace highlighting**: Click event → highlight all events with same `trace_id`
- **Auto-refresh**: 10-second polling (fallback mode)
- **Recent events table**: Last 12 events with JSON detail view
- **Responsive design** with Tailwind CSS

**WebSocket Integration (PR-42)**
- `frontend/panel/src/lib/ws.ts`: WebSocket client helper
  - Auto-reconnect with exponential backoff (1s → 10s max)
  - Connection lifecycle management
  - Error handling and graceful disconnect
- Timeline WebSocket integration
  - **Connection status badge**: `connected` / `connecting` / `disconnected`
  - **Live toggle checkbox**: Enable/disable real-time streaming
  - **Real-time event updates**: No refresh needed (< 100ms latency)
  - **1500 event buffer**: Memory-safe in-browser storage
  - **Fallback polling**: 10s interval when WebSocket disabled
  - **Smart reconnect**: Reconnects when filters change

---

## 🧪 Doğrulama

```bash
# 1. Start services
make docker-up

# 2. Seed test data
docker exec levibot-api python3 -m backend.src.testing.seed_data today

# 3. Test smart filters
curl 'http://localhost:8000/events?event_type=SIGNAL_SCORED&limit=5' | jq
curl 'http://localhost:8000/events?symbol=BTCUSDT&q=confidence&limit=10' | jq

# 4. Check WebSocket metrics
curl -s http://localhost:8000/metrics/prom | grep levibot_ws

# 5. Open Panel
open http://localhost:3001
# Check: Timeline shows "connected" badge (green)
# Check: Events appear in real-time as they're logged
# Check: Trace highlighting works on click
```

---

## ⚠️ Known Limitations & Notes

* **Backpressure Handling**: High-volume scenarios may drop messages when subscriber queues are full (by design for system stability).
* **In-Memory Pub/Sub**: Current implementation uses in-process pub/sub. For distributed/persistent streaming, replace `BUS` with Redis pub/sub or Kafka.
* **Browser Buffer**: Timeline keeps max 1500 events in memory to prevent performance degradation.
* **WebSocket Filters**: Filters are applied server-side; client receives only matching events.

---

## 🔄 Breaking Changes

None. This release is fully backward compatible with v1.5.0.

---

## 📊 Migration Guide

No migration needed. Simply pull the latest code and rebuild Docker images:

```bash
git pull origin main
make docker-down
make docker-build
make docker-up
```

---

## 🎯 What's Next (v1.7.0 Roadmap)

**Potential Features:**
- **PR-43**: Event Replay & Debug Mode (time travel, slow-motion playback)
- **PR-44**: Analytics Dashboard (event stats, time-series charts, aggregations)
- **PR-45**: Advanced Search (Elasticsearch integration for full-text search)
- **PR-46**: Event Notifications (browser push, toast alerts)

---

## 🙏 Contributors

- @siyahkare - Core development
- AI Assistant - Pair programming & architecture

---

## 📜 Full Changelog

**v1.6.0 (Oct 6, 2025)**
- feat(PR-40): Smart event filters for `/events` endpoint
- feat(PR-41): Interactive Event Timeline UI with Recharts
- feat(PR-42): Real-time WebSocket event streaming
- docs: Update README with filter examples and WebSocket usage
- chore: Add WebSocket metrics to Prometheus

**Previous Releases**
- [v1.5.0](RELEASE_NOTES_v1.5.0.md) - Webhook & Alerting + Production Docker
- [v1.4.0](RELEASE_NOTES_v1.4.0.md) - Developer Experience Polish
- [v1.3.0](RELEASE_NOTES_v1.3.0.md) - Lifespan Handlers + Build Metrics
- [v1.2.0](RELEASE_NOTES_v1.2.0.md) - S3 Log Archiver
- [v1.1.0](RELEASE_NOTES_v1.1.0.md) - CI/CD + Security
- [v1.0.0](RELEASE_NOTES_v1.0.0.md) - Initial MVP Release

---

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

