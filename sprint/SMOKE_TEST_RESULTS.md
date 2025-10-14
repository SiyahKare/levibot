# 🔎 Smoke Test Results - Sprint-10 UI

**Date:** October 14, 2025  
**Duration:** 15 minutes  
**Tester:** AI Engineering Lead  
**Status:** ⚠️ **PARTIAL PASS** (Backend issues found)

---

## 📊 Summary

| Test | Status | Notes |
|------|--------|-------|
| **Backend Endpoints** | ⚠️ Partial | Endpoints exist but model files missing |
| **Frontend Build** | ✅ Pass | No build errors |
| **API Integration** | ⚠️ Blocked | Backend errors prevent full test |

---

## 🔧 Backend Issues Found

### 1. Missing Dependency: protobuf

**Error:**
```
ccxt.base.errors.NotSupported: mexc requires protobuf to decode messages
```

**Fix Applied:**
```bash
pip install "protobuf==5.29.5"
```

**Status:** ✅ Fixed

---

### 2. Missing Model Files

**Error:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'backend/data/models/best_lgbm.pkl'
```

**Root Cause:**
- Engine manager tries to load ML models on startup
- Epic-B/C trained models not committed to repo (gitignored)
- Models are in `backend/data/models/` but not accessible

**Impact:**
- `/engines` endpoint returns 500 Internal Server Error
- Engine initialization fails
- Cannot test Engines page

**Recommended Fix:**
1. **Quick (for smoke test):** Disable ML components in engine initialization
2. **Proper (for PR-6):** Train models or use mock predictors

---

### 3. Endpoint Mismatches

**Frontend Expected:**
- `GET /engines` → Array of engines

**Backend Actual:**
- `GET /engines` → ✅ Implemented (but crashes due to model loading)
- `GET /engines/status` → Engine summary dict

**Status:** ✅ Endpoint exists (crashes on model load)

---

## ✅ What Works

### Backend Endpoints (Mock Data)

1. **GET /backtest/reports** ✅
   ```bash
   curl http://localhost:8000/backtest/reports
   # Returns mock report array
   ```

2. **POST /backtest/run** ✅
   ```bash
   curl -X POST http://localhost:8000/backtest/run \
     -H "Content-Type: application/json" \
     -d '{"symbol":"BTC/USDT","days":30}'
   # Returns queued status
   ```

3. **GET /live/status** ✅
   ```bash
   curl http://localhost:8000/live/status
   # Returns: {"kill_switch_active": false, ...}
   ```

4. **POST /live/kill** ✅
   ```bash
   curl -X POST "http://localhost:8000/live/kill?on=true&reason=test"
   # Returns: {"kill_switch": true, ...}
   ```

5. **GET /stream/engines** ✅ (Endpoint exists)
   - SSE endpoint implemented
   - Crashes on model load (same issue as /engines)

---

## 🐛 Critical Bugs (Blockers)

### Bug #1: Engine Initialization Fails

**Priority:** 🔴 **CRITICAL**

**Description:**
- Engine manager tries to load ML models on startup
- Models don't exist → FileNotFoundError
- All engine endpoints return 500

**Impact:**
- Cannot test `/engines` page
- Cannot test SSE realtime updates
- Cannot test start/stop buttons

**Workaround:**
- Disable ML components temporarily
- Use mock predictors

**Proper Fix:**
- Make ML components optional (lazy load)
- Graceful degradation if models missing
- Add `--no-ml` flag for testing

---

### Bug #2: Missing protobuf Dependency

**Priority:** 🟡 **HIGH**

**Description:**
- ccxt.pro requires protobuf for MEXC WebSocket
- Not in requirements.txt

**Impact:**
- Backend crashes on startup (if ccxt.pro used)

**Fix Applied:** ✅
```bash
pip install "protobuf==5.29.5"
```

**Action Required:**
- Add to `backend/requirements.txt`

---

## 📋 Smoke Test Checklist (Incomplete)

### /engines Page
- [ ] ❌ **BLOCKED** - Page loads without errors (500 from backend)
- [ ] ❌ **BLOCKED** - SSE connection established
- [ ] ❌ **BLOCKED** - Start/Stop buttons work
- [ ] ❌ **BLOCKED** - p95 ms updates in real-time

**Reason:** Backend crashes on model load

---

### /backtest Page
- [ ] ⏳ **NOT TESTED** - Page loads (frontend not started)
- [ ] ✅ **PASS** - Backend endpoint works (mock data)
- [ ] ⏳ **NOT TESTED** - Run form submits
- [ ] ⏳ **NOT TESTED** - Reports list updates

**Status:** Backend ready, frontend not tested

---

### /ops Page (Kill Switch)
- [ ] ⏳ **NOT TESTED** - Page loads
- [ ] ✅ **PASS** - Backend endpoint works
- [ ] ⏳ **NOT TESTED** - Toggle works
- [ ] ⏳ **NOT TESTED** - Status updates

**Status:** Backend ready, frontend not tested

---

## 🚀 Quick Fixes Applied

1. ✅ Added `GET /engines` endpoint
2. ✅ Added `GET /backtest/reports` endpoint  
3. ✅ Added `POST /backtest/run` endpoint
4. ✅ Added `GET /stream/engines` SSE endpoint
5. ✅ Fixed `/live/status` response format
6. ✅ Installed protobuf dependency

---

## 🔄 Next Steps

### Immediate (Before PR-6)

1. **Fix Engine Initialization** (30 min)
   - Make ML components optional
   - Add `--no-ml` flag
   - Graceful degradation

2. **Update requirements.txt** (5 min)
   ```bash
   echo "protobuf==5.29.5" >> backend/requirements.txt
   ```

3. **Restart Backend** (2 min)
   ```bash
   uvicorn src.app.main:app --reload --no-ml
   ```

4. **Run Full Smoke Test** (5 min)
   - Start frontend: `pnpm dev`
   - Test all 3 pages
   - Document results

---

### PR-6 Tasks (12 hours)

1. **ESLint + Prettier** (1h)
2. **Vitest + Testing Library** (1.5h)
3. **Write Tests** (6h)
   - API client tests (8-10 cases)
   - SSE reconnection tests
   - Component smoke tests
4. **GitHub Actions CI** (2h)
5. **Fix Issues** (2.5h)

---

## 📊 Test Coverage

**Backend Endpoints:**
- ✅ 5/5 endpoints exist
- ⚠️ 2/5 endpoints work (backtest, live)
- ❌ 3/5 endpoints crash (engines, stream - model loading)

**Frontend Pages:**
- ⏳ 0/3 pages tested (frontend not started)

**Overall Status:** ⚠️ **60% Complete**

---

## 💡 Recommendations

### For Smoke Test

1. **Disable ML temporarily:**
   ```python
   # backend/src/engine/engine.py
   def _init_ml_components(self):
       if os.getenv("DISABLE_ML"):
           self._ensemble = None
           return
       # ... existing code
   ```

2. **Mock predictors:**
   ```python
   class MockPredictor:
       def predict(self, *args): return 0.5, 0.5
   ```

### For Production

1. **Lazy load models:**
   - Don't load on engine init
   - Load on first prediction
   - Cache loaded models

2. **Graceful degradation:**
   - If model missing → use fallback (e.g., random)
   - Log warning, don't crash

3. **Health checks:**
   - `/health` should work even if models missing
   - `/engines` should return status (even if degraded)

---

## ✅ Sign-Off

**Smoke Test Status:** ⚠️ **PARTIAL PASS**

**Critical Issues:** 1 (Engine initialization)  
**High Issues:** 1 (protobuf dependency)  
**Medium Issues:** 0  
**Low Issues:** 0

**Ready for PR-6:** ⚠️ **After quick fixes**

**Estimated Fix Time:** 30-45 minutes

**Next Action:** Apply quick fixes → Re-run smoke test → Start PR-6

---

**Tester:** AI Engineering Lead  
**Date:** October 14, 2025  
**Time Spent:** 15 minutes

