# 🧪 Smoke Test Checklist - Sprint-10 UI

**Test Date:** October 14, 2025  
**Tester:** Developer  
**Environment:** Local (`pnpm dev` + backend on `localhost:8000`)

---

## ✅ Pre-Test Setup

1. **Backend Running:**
   ```bash
   cd /Users/onur/levibot/backend
   source venv/bin/activate
   uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Frontend Running:**
   ```bash
   cd /Users/onur/levibot/frontend/panel
   cp .env.example .env.local
   pnpm install
   pnpm dev
   # Open http://localhost:5173
   ```

3. **Expected State:**
   - Backend API responding on `http://localhost:8000`
   - Frontend dev server on `http://localhost:5173`
   - No console errors on page load

---

## 🔧 Test Cases

### 1. Engines Page (`/engines`)

**Steps:**
1. Navigate to http://localhost:5173/engines
2. Check page loads without errors
3. Verify table renders (even if empty)
4. If engines exist:
   - Check status badges (running/degraded/stopped)
   - Check metrics display (p95, uptime, trades)
   - Click "Start" button → Should show toast notification
   - Click "Stop" button → Should show toast notification
5. Open DevTools Network tab → Verify SSE connection (`/stream/engines`)

**Expected:**
- ✅ Page loads successfully
- ✅ SSE connection established (EventSource)
- ✅ Table renders with engine rows OR empty state
- ✅ Buttons are disabled/enabled based on status
- ✅ Toast notifications appear on actions
- ✅ Real-time updates (if SSE working)

**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

**Notes:**
_____________________________________________________

---

### 2. Backtest Page (`/backtest`)

**Steps:**
1. Navigate to http://localhost:5173/backtest
2. Check page loads without errors
3. Verify form fields:
   - Symbol input (default: BTC/USDT)
   - Days input (default: 30)
   - Fee bps input (default: 5)
   - Slippage bps input (default: 5)
   - Max position input (default: 1.0)
4. Fill form and click "Run Backtest"
5. Check "Recent Reports" section updates
6. If reports exist:
   - Verify metrics display (Sharpe, Sortino, MDD, Win Rate, Ann Return, Trades)
   - Click "Report" link → Should open Markdown report
   - Click "JSON" link → Should download JSON file

**Expected:**
- ✅ Page loads successfully
- ✅ Form fields editable
- ✅ "Run Backtest" button works
- ✅ Reports list updates after run
- ✅ Metrics display correctly
- ✅ Links work (Markdown + JSON)
- ✅ Empty state if no reports

**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

**Notes:**
_____________________________________________________

---

### 3. Ops Page (`/ops`) - Kill Switch

**Steps:**
1. Navigate to http://localhost:5173/ops
2. Scroll to "Kill Switch" section
3. Check kill switch status badge
4. Enter reason (e.g., "manual_test")
5. Click "Activate Kill Switch" → Confirm prompt
6. Verify status updates to "ACTIVE"
7. Click "Deactivate Kill Switch"
8. Verify status updates to "INACTIVE"

**Expected:**
- ✅ Kill switch section visible
- ✅ Status badge shows current state
- ✅ Reason input field works
- ✅ Activate button triggers confirmation
- ✅ Status updates after activation
- ✅ Deactivate button works
- ✅ Toast notifications appear
- ✅ SWR polling (status updates every 5s)

**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

**Notes:**
_____________________________________________________

---

### 4. Navigation Links

**Steps:**
1. Check top navigation bar
2. Verify new links present:
   - "🔧 Engines"
   - "📊 Backtest"
3. Click each link → Should navigate without errors
4. Check active state (highlighted link)

**Expected:**
- ✅ "Engines" link visible
- ✅ "Backtest" link visible
- ✅ Links navigate correctly
- ✅ Active state highlights current page

**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

**Notes:**
_____________________________________________________

---

### 5. API Integration

**Steps:**
1. Open DevTools Network tab
2. Navigate to `/engines`
3. Check network requests:
   - GET `/engines` (initial load)
   - EventSource `/stream/engines` (SSE)
4. Navigate to `/backtest`
5. Check network requests:
   - GET `/backtest/reports` (initial load)
   - POST `/backtest/run` (after form submission)
6. Navigate to `/ops`
7. Check network requests:
   - GET `/live/status` (kill switch status)
   - POST `/live/kill` (after button click)

**Expected:**
- ✅ API calls use correct endpoints
- ✅ Requests include `credentials: include`
- ✅ JSON content-type header
- ✅ Responses parsed correctly
- ✅ Errors handled gracefully (toast notifications)

**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

**Notes:**
_____________________________________________________

---

### 6. Dark Mode

**Steps:**
1. Toggle dark mode (top-right toggle)
2. Navigate to `/engines`
3. Check styling (dark background, light text)
4. Navigate to `/backtest`
5. Check form fields (dark mode styling)
6. Navigate to `/ops`
7. Check kill switch section (dark mode)

**Expected:**
- ✅ Dark mode toggle works
- ✅ All pages support dark mode
- ✅ Text readable in dark mode
- ✅ Form fields styled correctly
- ✅ Buttons styled correctly
- ✅ Tables styled correctly

**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

**Notes:**
_____________________________________________________

---

### 7. Error Handling

**Steps:**
1. Stop backend server
2. Navigate to `/engines`
3. Check error toast appears
4. Navigate to `/backtest`
5. Try to run backtest → Should show error toast
6. Navigate to `/ops`
7. Try to toggle kill switch → Should show error toast
8. Check console for errors

**Expected:**
- ✅ Error toasts appear on API failures
- ✅ Pages don't crash (ErrorBoundary)
- ✅ Loading states show during requests
- ✅ Empty states show when no data
- ✅ Console errors are logged (not silent)

**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

**Notes:**
_____________________________________________________

---

### 8. Loading States

**Steps:**
1. Restart backend
2. Navigate to `/engines`
3. Check loading skeleton appears briefly
4. Navigate to `/backtest`
5. Click "Run Backtest" → Check "Running..." state
6. Click "Refresh" → Check disabled state

**Expected:**
- ✅ Loading skeletons appear on initial load
- ✅ Button disabled during async operations
- ✅ "Running..." text shows during backtest
- ✅ Spinner or loading indicator visible

**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

**Notes:**
_____________________________________________________

---

### 9. Empty States

**Steps:**
1. Ensure backend has no engines configured
2. Navigate to `/engines`
3. Check empty state message
4. Ensure backend has no backtest reports
5. Navigate to `/backtest`
6. Check empty state message

**Expected:**
- ✅ Empty state for engines (helpful message)
- ✅ Empty state for backtest reports (helpful message)
- ✅ Empty states include icon/emoji
- ✅ Empty states guide user on next steps

**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

**Notes:**
_____________________________________________________

---

## 📊 Summary

**Total Test Cases:** 9  
**Passed:** ___  
**Failed:** ___  
**Not Tested:** ___  

**Critical Issues:**
_____________________________________________________
_____________________________________________________

**Minor Issues:**
_____________________________________________________
_____________________________________________________

**Recommendations:**
_____________________________________________________
_____________________________________________________

---

## ✅ Sign-Off

**Tester:** _________________  
**Date:** _________________  
**Status:** ⬜ Approved | ⬜ Needs Fixes | ⬜ Blocked  

**Notes:**
_____________________________________________________
_____________________________________________________

