# 🧪 Mini Bug-Bash Checklist (15 min)

**Date:** October 14, 2025  
**Goal:** Find edge cases, errors, UX issues before PR-6

---

## 🔍 Test Scenarios

### 1. Error Handling (5 min)

**Scenario A: Backend Down**
- [ ] Stop backend server
- [ ] Navigate to `/engines`
- [ ] **Expected:** Error toast appears, page doesn't crash
- [ ] **Expected:** Empty state or loading skeleton (no white screen)
- [ ] Navigate to `/backtest`
- [ ] Click "Run Backtest"
- [ ] **Expected:** Error toast with message
- [ ] Navigate to `/ops`
- [ ] Toggle kill switch
- [ ] **Expected:** Error toast, button re-enables

**Scenario B: API Timeout**
- [ ] Restart backend
- [ ] Open DevTools Network → Throttle to "Slow 3G"
- [ ] Navigate to `/engines`
- [ ] **Expected:** Loading state shows, timeout after 30s?
- [ ] **Expected:** Error toast or retry UI

**Scenario C: 404/500 Errors**
- [ ] Modify API endpoint (e.g., `/engines` → `/enginesx`)
- [ ] Navigate to `/engines`
- [ ] **Expected:** Error toast with status code
- [ ] **Expected:** ErrorBoundary catches crash (if any)

**Status:** ⬜ Pass | ⬜ Fail

**Issues Found:**
```

```

---

### 2. SSE Reconnection (3 min)

**Scenario: Connection Drop**
- [ ] Navigate to `/engines`
- [ ] Check SSE connected (DevTools Network)
- [ ] Stop backend for 5s
- [ ] Restart backend
- [ ] **Expected:** SSE reconnects within 2s
- [ ] **Expected:** Real-time updates resume
- [ ] **Expected:** No duplicate connections (check Network tab)

**Scenario: Long Disconnect**
- [ ] Navigate to `/engines`
- [ ] Stop backend for 30s
- [ ] **Expected:** Exponential backoff (2s, 3.6s, 6.5s, 10s max)
- [ ] Restart backend
- [ ] **Expected:** SSE reconnects

**Status:** ⬜ Pass | ⬜ Fail

**Issues Found:**
```

```

---

### 3. Environment & Fallbacks (2 min)

**Scenario A: Missing .env**
- [ ] Rename `.env.local` to `.env.local.bak`
- [ ] Restart `pnpm dev`
- [ ] **Expected:** `VITE_API_BASE` falls back to `http://localhost:8000`
- [ ] **Expected:** Console warning about missing env?

**Scenario B: Invalid API Base**
- [ ] Set `VITE_API_BASE=http://invalid:9999`
- [ ] Restart `pnpm dev`
- [ ] Navigate to `/engines`
- [ ] **Expected:** Error toast, no crash
- [ ] **Expected:** Empty state or error message

**Status:** ⬜ Pass | ⬜ Fail

**Issues Found:**
```

```

---

### 4. Dark Mode Accessibility (3 min)

**WCAG AA Contrast Check:**
- [ ] Toggle dark mode ON
- [ ] Navigate to `/engines`
- [ ] **Check:** Text readable on dark background? (Contrast ≥4.5:1)
- [ ] **Check:** Table borders visible?
- [ ] **Check:** Status badges readable (running/degraded/stopped)?
- [ ] Navigate to `/backtest`
- [ ] **Check:** Form inputs readable (text + placeholder)?
- [ ] **Check:** Metrics text readable (Sharpe, MDD, etc.)?
- [ ] Navigate to `/ops`
- [ ] **Check:** Kill switch section readable?

**Color Blind Test (Optional):**
- [ ] Use browser extension (e.g., "Colorblind Web Page Filter")
- [ ] Check status colors distinguishable (green/amber/red)

**Status:** ⬜ Pass | ⬜ Fail

**Issues Found:**
```

```

---

### 5. Empty States (2 min)

**Scenario A: No Engines**
- [ ] Ensure backend has no engines configured
- [ ] Navigate to `/engines`
- [ ] **Expected:** Empty state with icon + message
- [ ] **Expected:** Message guides user (e.g., "Add symbols to backend/src/app/main.py")

**Scenario B: No Reports**
- [ ] Ensure backend has no backtest reports
- [ ] Navigate to `/backtest`
- [ ] **Expected:** Empty state with icon + message
- [ ] **Expected:** Message guides user (e.g., "Run your first backtest")

**Scenario C: API Returns Empty Array**
- [ ] Mock API to return `{"ok": true, "items": []}`
- [ ] **Expected:** Empty state shows (not "Loading...")

**Status:** ⬜ Pass | ⬜ Fail

**Issues Found:**
```

```

---

### 6. Optimistic UI & Disabled States (2 min)

**Scenario: Start/Stop Buttons**
- [ ] Navigate to `/engines`
- [ ] Click "Start" on stopped engine
- [ ] **Expected:** Button disabled immediately
- [ ] **Expected:** Button text changes? (e.g., "Starting...")
- [ ] Wait for API response
- [ ] **Expected:** Button re-enables
- [ ] **Expected:** Status badge updates

**Scenario: Backtest Run**
- [ ] Navigate to `/backtest`
- [ ] Click "Run Backtest"
- [ ] **Expected:** Button disabled + "Running..." text
- [ ] **Expected:** Button re-enables after API response
- [ ] **Expected:** No double-submit if clicked twice

**Scenario: Kill Switch**
- [ ] Navigate to `/ops`
- [ ] Click "Activate Kill Switch"
- [ ] **Expected:** Confirm dialog appears
- [ ] Click "Cancel"
- [ ] **Expected:** No API call (check Network tab)
- [ ] Click "Activate" again → Confirm "OK"
- [ ] **Expected:** Button disabled during request
- [ ] **Expected:** Status updates after response

**Status:** ⬜ Pass | ⬜ Fail

**Issues Found:**
```

```

---

## 🎨 UX Polish Checks

### Visual Quality
- [ ] Loading skeletons match content layout
- [ ] Toast notifications auto-dismiss (5s default?)
- [ ] Toast notifications stack correctly (multiple at once)
- [ ] Hover states on buttons (darker shade)
- [ ] Focus states on inputs (ring/outline)
- [ ] Table rows hover effect

### Responsive Design (Quick Check)
- [ ] Resize browser to 1024px width
- [ ] **Expected:** Table scrolls horizontally (no layout break)
- [ ] Resize to 768px
- [ ] **Expected:** Navigation wraps or collapses
- [ ] Resize to 375px (mobile)
- [ ] **Expected:** All content accessible (no hidden buttons)

---

## 🐛 Bug Summary

**Critical (Blockers):**
```
1. 
2. 
3. 
```

**High (Must Fix Before PR-6):**
```
1. 
2. 
3. 
```

**Medium (Fix in PR-6):**
```
1. 
2. 
3. 
```

**Low (Nice to Have):**
```
1. 
2. 
3. 
```

---

## 📊 Test Summary

**Total Scenarios:** 6  
**Passed:** ___ / 6  
**Failed:** ___ / 6  
**Issues Found:** ___  

**Time Spent:** ___ min  
**Status:** ⬜ Ready for PR-6 | ⬜ Needs Fixes

---

## 🚀 Next Steps

**If All Pass:**
- [ ] Commit quick fixes (if any)
- [ ] Start PR-6: ESLint + Prettier + Vitest
- [ ] Add tests for found edge cases

**If Issues Found:**
- [ ] Prioritize critical bugs
- [ ] Create GitHub issues for medium/low
- [ ] Fix high-priority bugs
- [ ] Re-run bug bash

---

## 📝 Notes

**Good Findings:**
```

```

**Surprising Behaviors:**
```

```

**Suggestions for PR-6:**
```

```

