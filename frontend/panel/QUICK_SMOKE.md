# 🔎 Quick Smoke Test (5 min)

**Date:** October 14, 2025  
**Goal:** Verify Sprint-10 UI works with live backend

---

## 🚀 Setup

**Terminal 1 - Backend:**
```bash
cd /Users/onur/levibot/backend
source venv/bin/activate
uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend:**
```bash
cd /Users/onur/levibot/frontend/panel
cp .env.example .env.local
pnpm install
pnpm dev
# Open http://localhost:5173
```

---

## ✅ Quick Checks

### 1. Engines (`/engines`) - 2 min

**Test:**
- Navigate to http://localhost:5173/engines
- Check SSE connection (DevTools Network → EventSource)
- Click "Start" on any engine → Toast appears?
- Wait 5s → p95 ms updates in real-time?
- Click "Stop" → Toast appears?

**Expected:**
- ✅ Page loads, table visible
- ✅ SSE connected (EventSource in Network tab)
- ✅ Buttons work (toast notifications)
- ✅ Real-time updates (p95, uptime, trades)
- ✅ Empty state if no engines configured

**Status:** ⬜ Pass | ⬜ Fail

**Notes:**
```

```

---

### 2. Backtest (`/backtest`) - 2 min

**Test:**
- Navigate to http://localhost:5173/backtest
- Fill form: BTC/USDT, 30 days, 5 fee bps, 5 slippage bps, 1.0 max pos
- Click "Run Backtest" → Wait 10-30s
- Click "Refresh" → Report appears in list?
- Click "Report" link → Markdown opens?
- Click "JSON" link → JSON downloads?

**Expected:**
- ✅ Form fields work
- ✅ "Run Backtest" triggers backend
- ✅ Reports list updates after run
- ✅ Metrics display (Sharpe, MDD, etc.)
- ✅ Links work (Markdown + JSON)
- ✅ Empty state if no reports

**Status:** ⬜ Pass | ⬜ Fail

**Notes:**
```

```

---

### 3. Ops - Kill Switch (`/ops`) - 1 min

**Test:**
- Navigate to http://localhost:5173/ops
- Scroll to "Kill Switch" section
- Enter reason: "smoke_test"
- Click "Activate Kill Switch" → Confirm
- Wait 5s → Status badge updates?
- Click "Deactivate Kill Switch"
- Status badge updates?

**Expected:**
- ✅ Kill switch section visible
- ✅ Reason input works
- ✅ Activate button works (toast + confirmation)
- ✅ Status updates after activation (5s polling)
- ✅ Deactivate button works
- ✅ Toast notifications appear

**Status:** ⬜ Pass | ⬜ Fail

**Notes:**
```

```

---

## 🎯 Quick Checklist

- [ ] All 3 pages load without console errors
- [ ] SSE connection established (`/stream/engines`)
- [ ] API calls use correct endpoints (`/engines`, `/backtest/run`, `/live/kill`)
- [ ] Toast notifications appear on all actions
- [ ] Dark mode works on all pages
- [ ] Navigation links work (🔧 Engines, 📊 Backtest)

---

## 🐛 Found Issues

**Critical:**
```

```

**Minor:**
```

```

---

## ✅ Summary

**Total Time:** ___ min  
**Passed:** ___ / 3  
**Status:** ⬜ All Pass | ⬜ Has Issues

**Next Steps:**
- [ ] Fix critical issues
- [ ] Run full smoke test (9 test cases)
- [ ] PR-6: Linting + Testing
- [ ] PR-7: Auth Upgrade

