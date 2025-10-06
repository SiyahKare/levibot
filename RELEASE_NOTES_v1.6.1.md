# LeviBot v1.6.1 — Analytics Dashboard

**Release Date:** October 6, 2025  
**Type:** Feature Addition (Patch Release)

## 🎯 What's New

### Analytics API (Backend)

**Three new endpoints for event analytics:**

1. **`GET /analytics/stats`** — Event distribution & top symbols
   ```json
   {
     "total": 1245,
     "event_types": {
       "SIGNAL_SCORED": 456,
       "AUTO_ROUTE_EXECUTED": 234,
       "POSITION_CLOSED": 178
     },
     "symbols": {
       "BTCUSDT": 145,
       "ETHUSDT": 98
     }
   }
   ```

2. **`GET /analytics/timeseries`** — Time-series with bucketing
   - Supported intervals: `1m`, `5m`, `15m`, `1h`
   - Returns time-bucketed event counts
   ```json
   {
     "interval": "5m",
     "points": [
       {"ts": "2025-10-06T14:00:00Z", "count": 12},
       {"ts": "2025-10-06T14:05:00Z", "count": 18}
     ]
   }
   ```

3. **`GET /analytics/traces`** — Top active traces
   - Ranked by event count and duration
   - Includes first/last timestamps
   ```json
   {
     "total": 45,
     "rows": [
       {
         "trace_id": "abc123",
         "event_count": 8,
         "first_ts": "2025-10-06T14:00:00Z",
         "last_ts": "2025-10-06T14:02:25Z",
         "duration_sec": 145
       }
     ]
   }
   ```

### Analytics Dashboard (Frontend)

**New Panel page with 4 interactive visualizations:**

1. **Event Type Distribution** — Pie Chart
   - Visual breakdown of event types
   - Color-coded with 10 distinct colors
   - Shows total event count

2. **Events Timeline** — Line Chart
   - Time-series with configurable bucketing (1m/5m/15m/1h)
   - Smooth line interpolation
   - Interactive tooltips

3. **Top Symbols** — Bar Chart
   - Top 10 most active symbols
   - Sorted by event count
   - Horizontal bar layout

4. **Top Traces** — Data Table
   - Top 20 traces by activity
   - Shows event count, duration, timestamps
   - Sortable columns

**Dashboard Features:**
- ✅ **Auto-refresh**: Updates every 30 seconds
- ✅ **Dynamic filters**:
  - Days: 1 / 7 / 30
  - Interval: 1m / 5m / 15m / 1h
  - Event type: CSV input (e.g., "SIGNAL_SCORED,POSITION_CLOSED")
- ✅ **Loading states**: Shows spinner during data fetch
- ✅ **Error handling**: Displays user-friendly error messages
- ✅ **Responsive design**: Works on mobile and desktop

### Documentation

- Updated `README.md` with Analytics Dashboard section
- Added API endpoint examples
- Documented dashboard features and filters

---

## 💡 Why It Matters

**Completes the "Living System" Vision:**
- **Flow**: Real-time event streaming (v1.6.0 / PR-42)
- **Timeline**: Interactive event visualization (v1.6.0 / PR-41)
- **Analytics**: Aggregated insights & trends (v1.6.1 / PR-44)

**Business Value:**
- **Investor-ready**: Single dashboard showing system activity at a glance
- **Operational insights**: Identify trends, bottlenecks, and anomalies
- **Debug-friendly**: Trace analysis helps troubleshoot complex flows

**Technical Excellence:**
- **Scalable**: Time-bucketing prevents performance issues with large datasets
- **Flexible**: Multiple time intervals support different analysis needs
- **Real-time**: 30s auto-refresh keeps dashboard current

---

## 🔄 Upgrade Instructions

### Docker (Recommended)
```bash
git pull origin main
make docker-build
make docker-up
```

### Manual
```bash
git pull origin main

# Backend
cd backend
pip install -r requirements.txt
# Restart uvicorn

# Frontend
cd frontend/panel
npm install
npm run build
```

---

## 🧪 Verification

```bash
# 1. Seed test data
docker exec levibot-api python3 -m backend.src.testing.seed_data today

# 2. Test API endpoints
curl -s 'http://localhost:8000/analytics/stats?days=1' | jq
curl -s 'http://localhost:8000/analytics/timeseries?interval=5m' | jq
curl -s 'http://localhost:8000/analytics/traces?limit=10' | jq

# 3. Open Panel
open http://localhost:3001
# Navigate to Analytics Dashboard
# Verify all 4 charts are visible and updating
```

---

## 📊 Technical Details

**Backend:**
- New router: `backend/src/app/routers/analytics.py` (+183 lines)
- Event aggregation from JSONL logs
- Time-bucketing algorithm for timeseries
- Trace grouping and ranking logic
- Unit tests: `backend/tests/test_analytics_basic.py`

**Frontend:**
- New page: `frontend/panel/src/pages/Analytics.tsx` (+147 lines)
- Recharts integration (Pie, Line, Bar charts)
- API helpers in `api.ts` (+40 lines)
- Responsive grid layout

**Total:** +370 lines of production code

---

## ⚠️ Breaking Changes

None. This release is fully backward compatible with v1.6.0.

---

## 🐛 Known Issues

None reported.

---

## 🔜 What's Next (v1.7.0 Preview)

**Potential features:**
- **PR-43**: Event Replay & Debug Mode (time travel, slow-motion playback)
- **PR-45**: Advanced Search (Elasticsearch integration)
- **PR-46**: Performance Metrics Dashboard (latency, throughput)
- **PR-47**: Multi-User Support (API key scoping, user sessions)

---

## 🙏 Contributors

- @siyahkare - Core development
- AI Assistant - Pair programming & architecture

---

## 📜 Full Changelog

**v1.6.1 (Oct 6, 2025)**
- feat(PR-44): Add Analytics Dashboard with stats/timeseries/traces endpoints
- feat: Add Event Type Distribution pie chart
- feat: Add Events Timeline line chart with bucketing
- feat: Add Top Symbols bar chart
- feat: Add Top Traces data table
- feat: Add auto-refresh and dynamic filters
- docs: Update README with Analytics section
- test: Add unit tests for analytics endpoints

**Previous Releases:**
- [v1.6.0](RELEASE_NOTES_v1.6.0.md) - Pulse: Event Intelligence + Real-time Stream
- [v1.5.0](RELEASE_NOTES_v1.5.0.md) - Webhook & Alerting + Production Docker
- [v1.4.0](RELEASE_NOTES_v1.4.0.md) - Developer Experience Polish
- [v1.3.0](RELEASE_NOTES_v1.3.0.md) - Lifespan Handlers + Build Metrics
- [v1.2.0](RELEASE_NOTES_v1.2.0.md) - S3 Log Archiver
- [v1.1.0](RELEASE_NOTES_v1.1.0.md) - CI/CD + Security
- [v1.0.0](RELEASE_NOTES_v1.0.0.md) - Initial MVP Release

---

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

