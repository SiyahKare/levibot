# LeviBot Web Panel – Current Status Audit

**Date:** 2025-10-14  
**Auditor:** Senior Full-Stack Engineer  
**Scope:** Frontend web panel inventory, quality, and Sprint-10/11 readiness

---

## 📊 Executive Summary

**Status:** ⚠️ **FUNCTIONAL BUT INCOMPLETE**

The LeviBot web panel is a **working React/Vite SPA** with:

- ✅ **20+ pages** covering strategies, ML, paper trading, Telegram, analytics
- ✅ **Realtime data** via WebSocket (with auto-reconnect)
- ✅ **Kill switch** and operational controls
- ⚠️ **NO tests** (0% coverage)
- ⚠️ **NO authentication** (admin key in code, no JWT/refresh)
- ⚠️ **Missing Sprint-10 features** (engines control, backtest UI, model cards, billing)
- ⚠️ **No CI/CD** for frontend

**Recommendation:** 3-5 day sprint to add Sprint-10 integrations + basic tests before production.

---

## 🏗️ Stack & Architecture

### Framework & Build

| Component      | Technology   | Version | Notes                            |
| -------------- | ------------ | ------- | -------------------------------- |
| **Framework**  | React        | 18.3.1  | Functional components, hooks     |
| **Build Tool** | Vite         | 5.4.8   | Fast HMR, ESM-based              |
| **Language**   | TypeScript   | 5.5.4   | Strict mode enabled ✅           |
| **Routing**    | React Router | 7.9.4   | Client-side SPA routing          |
| **Styling**    | TailwindCSS  | 3.4.10  | Utility-first, dark mode support |

### State & Data Fetching

| Component            | Technology              | Notes                                             |
| -------------------- | ----------------------- | ------------------------------------------------- |
| **State Management** | React hooks             | No Redux/Zustand (simple local state)             |
| **Data Fetching**    | SWR                     | 2.3.6 - Stale-while-revalidate, auto-refresh      |
| **API Client**       | Custom `http()`         | `src/lib/api.ts` - fetch wrapper with types       |
| **WebSocket**        | Custom `makeWsClient()` | `src/lib/ws.ts` - auto-reconnect with exp backoff |
| **Notifications**    | Sonner                  | 2.0.7 - Toast notifications                       |

### UI Components

| Component          | Source           | Notes                                 |
| ------------------ | ---------------- | ------------------------------------- |
| **Charts**         | Recharts         | 2.15.4 - Line, Bar, Area charts       |
| **Date Picker**    | react-day-picker | 9.11.1 - Date range selection         |
| **Dark Mode**      | Custom toggle    | localStorage persistence              |
| **Error Boundary** | Custom           | `src/components/ui/ErrorBoundary.tsx` |
| **Skeleton**       | Custom           | `src/components/ui/Skeleton.tsx`      |

---

## 📁 Feature Inventory

### Pages & Routes (24 total)

| Route                | Component              | Purpose                        | Backend Endpoints                       | Status             |
| -------------------- | ---------------------- | ------------------------------ | --------------------------------------- | ------------------ |
| `/`                  | `Overview.tsx`         | Dashboard, equity, AI status   | `/healthz`, `/ai/predict`, `/ai/models` | ✅ Working         |
| `/ml`                | `MLDashboard.tsx`      | ML model controls, predictions | `/ai/*`, `/analytics/predictions`       | ✅ Working         |
| `/paper`             | `Paper.tsx`            | Paper trading portfolio        | `/paper/*`                              | ✅ Working         |
| `/signals`           | `Signals.tsx`          | Signal log, live feed          | `/ops/signal_log`, WS `/ws/events`      | ✅ Working         |
| `/trades`            | `Trades.tsx`           | Trade history, export CSV      | `/analytics/trades/*`                   | ✅ Working         |
| `/strategies`        | `Strategies.tsx`       | Strategy enable/disable        | `/strategy/*`                           | ✅ Working         |
| `/risk`              | `Risk.tsx`             | Risk presets, guardrails       | `/risk/*`                               | ✅ Working         |
| `/scalp`             | `Scalp.tsx`            | LSE engine control             | `/lse/*`                                | ✅ Working         |
| `/daytrade`          | `Daytrade.tsx`         | Day engine control             | `/day/*`                                | ✅ Working         |
| `/swing`             | `Swing.tsx`            | Swing engine control           | `/swing/*`                              | ✅ Working         |
| `/rsi-macd`          | `RsiMacd.tsx`          | RSI+MACD strategy              | `/strategy/rsi_macd/*`                  | ✅ Working         |
| `/watchlist`         | `Watchlist.tsx`        | Symbol watchlist               | N/A (local state)                       | ✅ Working         |
| `/analytics`         | `Analytics.tsx`        | PnL by strategy, deciles       | `/analytics/*`                          | ✅ Working         |
| `/ai-brain`          | `AIBrain.tsx`          | AI explainer, regime detection | `/ai/*`                                 | ✅ Working         |
| `/alerts`            | `Alerts.tsx`           | Alert configuration            | `/alerts/*` (TODO)                      | ⚠️ Placeholder     |
| `/telegram`          | `TelegramSignals.tsx`  | Telegram signal feed           | `/telegram/*`                           | ✅ Working         |
| `/telegram/control`  | `TelegramControl.tsx`  | Telegram bot control           | `/telegram/status`                      | ✅ Working         |
| `/telegram/insights` | `TelegramInsights.tsx` | Telegram analytics             | `/telegram/*`                           | ⚠️ Placeholder     |
| `/telegram/settings` | `TelegramSettings.tsx` | Telegram config                | `/telegram/*`                           | ⚠️ Placeholder     |
| `/events`            | `EventsTimeline.tsx`   | Event timeline                 | WS `/ws/events`                         | ✅ Working         |
| `/mev`               | `MEVFeed.tsx`          | MEV opportunities              | `/mev/*` (TODO)                         | ❌ Not implemented |
| `/nft`               | `NFTSniper.tsx`        | NFT floor prices               | `/nft/*` (TODO)                         | ❌ Not implemented |
| `/onchain`           | `OnChain.tsx`          | On-chain metrics               | `/onchain/*` (TODO)                     | ❌ Not implemented |
| `/integrations`      | `Integrations.tsx`     | External integrations          | `/integrations/*` (TODO)                | ❌ Not implemented |
| `/ops`               | `Ops.tsx`              | Kill switch, canary, flags     | `/admin/*`, `/ops/*`                    | ✅ Working         |

### Components (30+ files)

| Component            | Path                              | Purpose                                  |
| -------------------- | --------------------------------- | ---------------------------------------- |
| **ErrorBoundary**    | `components/ui/ErrorBoundary.tsx` | Catch React errors                       |
| **Skeleton**         | `components/ui/Skeleton.tsx`      | Loading placeholders                     |
| **DarkModeToggle**   | `components/DarkModeToggle.tsx`   | Theme switcher                           |
| **SSEStatus**        | `components/SSEStatus.tsx`        | SSE connection indicator                 |
| **ReplayBadge**      | `components/ReplayBadge.tsx`      | Replay mode indicator                    |
| **TradeWidget**      | `components/TradeWidget.tsx`      | Quick trade form                         |
| **DateRange**        | `components/DateRange.tsx`        | Date range picker                        |
| **AI Components**    | `components/ai/*`                 | AI explainer, regime card, impact ticker |
| **ML Components**    | `components/ml/*`                 | Control bar, KPI cards, status banner    |
| **Chart Components** | Various                           | DEX sparkline, L2 yields, NFT floor      |

### API Client (`src/lib/api.ts`)

**Total Endpoints:** 60+

**Categories:**

- ✅ Health & Status (2)
- ✅ Admin & Flags (6)
- ✅ Risk Management (7)
- ✅ Strategies (2)
- ✅ Analytics (8)
- ✅ Ops & Monitoring (4)
- ✅ Signal Log (2)
- ✅ AI & ML (5)
- ✅ Paper Trading (5)
- ✅ Telegram (1)
- ✅ AI Reason (2)
- ✅ Admin Auth (2)
- ✅ LSE/Day/Swing Engines (15 each = 45)

**Missing Sprint-10 Endpoints:**

- ❌ `/engines/*` - Multi-engine manager (Epic-1)
- ❌ `/backtest/*` - Backtesting framework (Epic-D)
- ❌ `/live/kill` - New kill switch API (Epic-E)
- ❌ `/models/*` - Model card viewer (Epic-B/C)
- ❌ `/usage/*` - Usage tracking/billing (Sprint-11)

---

## 🔌 API & Realtime Wiring

### HTTP Client

**Location:** `src/lib/api.ts`

**Features:**

- ✅ Base URL from env (`VITE_API_BASE` or `http://localhost:8000`)
- ✅ Credentials: `include` (cookies for admin auth)
- ✅ JSON content-type
- ✅ Error handling (throws on non-2xx)
- ⚠️ **NO retry logic** (SWR handles retries)
- ⚠️ **NO request timeout**
- ⚠️ **NO rate limiting**

**Example:**

```typescript
export async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return (await res.json()) as T;
}
```

### WebSocket Client

**Location:** `src/lib/ws.ts`

**Features:**

- ✅ Auto-reconnect with exponential backoff (1s → 10s max)
- ✅ JSON message parsing
- ✅ Error handling (onError callback)
- ✅ Lifecycle hooks (onOpen, onClose, onMessage)
- ⚠️ **NO ping/pong** (relies on server keepalive)
- ⚠️ **NO message queue** (drops messages if disconnected)

**Backoff Logic:**

```typescript
delay = Math.min((delay * 1.8) | 0, opts.maxDelayMs ?? 10000);
```

**Usage Example:**

```typescript
// src/pages/Signals.tsx
makeWsClient({
  url: `ws://localhost:8000/ws/events?event_type=SIGNAL_SCORED`,
  onMessage: (data) => setSignals((prev) => [data, ...prev].slice(0, 50)),
  reconnectDelayMs: 1000,
  maxDelayMs: 10000,
});
```

### Data Fetching (SWR)

**Features:**

- ✅ Stale-while-revalidate pattern
- ✅ Auto-refresh intervals (5s-30s)
- ✅ Manual mutation (`mutate()`)
- ✅ Error retry (default 3x)
- ⚠️ **NO global error handler**
- ⚠️ **NO offline detection**

**Example:**

```typescript
const { data, error, mutate } = useSWR("/ai/models", api.aiModels, {
  refreshInterval: 15_000,
});
```

### Authentication

**Current State:** ⚠️ **BASIC ADMIN KEY**

**Implementation:**

- Admin key stored in `localStorage` (insecure)
- Cookie-based session after login
- **NO JWT/refresh tokens**
- **NO RBAC** (all users are admin)
- **NO session expiry handling**

**Code:**

```typescript
// src/pages/Ops.tsx
const handleAdminLogin = async () => {
  const result = await api.adminLogin(adminKey);
  if (result.ok) {
    localStorage.setItem("admin_key", adminKey);
    toast.success("Logged in");
  }
};
```

---

## 🧪 Code Quality

### TypeScript Coverage

**Status:** ✅ **GOOD**

- Strict mode enabled (`tsconfig.json`)
- Type definitions for API responses
- Path aliases (`@/*` → `src/*`)
- **No `any` abuse** (mostly typed)

**Gaps:**

- Some API responses use `any` (e.g., `flags`, `guardrails`)
- Missing types for WebSocket messages
- No shared type definitions with backend

### Linting & Formatting

**Status:** ❌ **NONE**

- **NO ESLint** config
- **NO Prettier** config
- **NO pre-commit hooks**
- Inconsistent code style (mix of `"` and `'`)

**Recommendation:** Add ESLint + Prettier + Husky

### Tests

**Status:** ❌ **ZERO COVERAGE**

- **NO unit tests** (Vitest/Jest)
- **NO integration tests** (Testing Library)
- **NO E2E tests** (Playwright/Cypress)
- **NO CI checks**

**Critical Gaps:**

- API client error handling untested
- WebSocket reconnect logic untested
- Component rendering untested
- Dark mode persistence untested

### Accessibility (a11y)

**Status:** ⚠️ **BASIC**

**Good:**

- ✅ Semantic HTML (`<header>`, `<main>`, `<nav>`)
- ✅ Button labels
- ✅ Dark mode support

**Missing:**

- ❌ ARIA labels for interactive elements
- ❌ Keyboard navigation (tab order)
- ❌ Focus management (modals, dropdowns)
- ❌ Screen reader testing
- ❌ Color contrast validation (WCAG AA)

### Performance

**Status:** ✅ **DECENT**

**Good:**

- ✅ Vite fast HMR
- ✅ Code splitting (React Router lazy loading potential)
- ✅ SWR caching

**Missing:**

- ❌ No `React.memo` for expensive components
- ❌ No `useMemo`/`useCallback` for heavy computations
- ❌ No `Suspense` for lazy loading
- ❌ No image optimization
- ❌ No bundle size analysis

### Error Handling

**Status:** ⚠️ **PARTIAL**

**Good:**

- ✅ ErrorBoundary component
- ✅ Toast notifications for user errors
- ✅ Try-catch in async handlers

**Missing:**

- ❌ No global error handler
- ❌ No error logging (Sentry/LogRocket)
- ❌ No retry UI for failed requests
- ❌ No offline mode detection

---

## 🚨 Gaps vs Sprint-10/11 Targets

### Sprint-10 Features (Missing)

| Feature                  | Backend Status       | Frontend Status | Gap                                   |
| ------------------------ | -------------------- | --------------- | ------------------------------------- |
| **Multi-Engine Manager** | ✅ Epic-1 Complete   | ❌ No UI        | Need `/engines` page + control panel  |
| **Backtesting UI**       | ✅ Epic-D Complete   | ❌ No UI        | Need `/backtest` page + report viewer |
| **Kill Switch (New)**    | ✅ Epic-E Complete   | ⚠️ Old API      | Update to `/live/kill` endpoint       |
| **Model Cards**          | ✅ Epic-B/C Complete | ❌ No UI        | Need model card viewer + metrics      |
| **Real Data Feed**       | ✅ Epic-A Complete   | ❌ No UI        | Need live ticker + gap-fill status    |

### Sprint-11 Targets (Planned)

| Feature               | Priority | Effort | Notes                         |
| --------------------- | -------- | ------ | ----------------------------- |
| **Usage Tracking**    | High     | 3 days | API key tiering, usage meters |
| **Billing UI**        | High     | 5 days | Stripe integration, invoices  |
| **User Management**   | High     | 3 days | RBAC, team invites            |
| **Model Marketplace** | Medium   | 7 days | Browse/buy custom models      |
| **Webhook Config**    | Low      | 2 days | Webhook endpoints UI          |

---

## ⚡ Quick Wins (≤1 Day)

### 1. Add Sprint-10 Endpoints (4 hours)

**File:** `src/lib/api.ts`

```typescript
// Add to api object:
engines: {
  list: () => http<any>("/engines"),
  start: (symbol: string) => http(`/engines/${symbol}/start`, { method: "POST" }),
  stop: (symbol: string) => http(`/engines/${symbol}/stop`, { method: "POST" }),
  health: (symbol: string) => http<any>(`/engines/${symbol}/health`),
},
backtest: {
  list: () => http<any>("/backtest/reports"),
  run: (params: any) => http<any>("/backtest/run", { method: "POST", body: JSON.stringify(params) }),
  report: (id: string) => http<any>(`/backtest/reports/${id}`),
},
live: {
  killStatus: () => http<any>("/live/status"),
  killToggle: (on: boolean, reason: string) =>
    http<any>(`/live/kill?on=${on}&reason=${reason}`, { method: "POST" }),
},
```

### 2. Update Kill Switch UI (2 hours)

**File:** `src/pages/Ops.tsx`

- Replace `/admin/kill` with `/live/kill`
- Add reason input field
- Show kill switch status badge
- Add auto-refresh for status

### 3. Add `.env.example` (30 minutes)

**File:** `frontend/panel/.env.example`

```bash
# API Base URL
VITE_API_BASE=http://localhost:8000

# Feature Flags
VITE_SHOW_TEST_ALERT=false
VITE_ENABLE_BACKTEST=true
VITE_ENABLE_BILLING=false
```

### 4. Add Basic Linting (2 hours)

```bash
npm install -D eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin
npm install -D prettier eslint-config-prettier eslint-plugin-react-hooks
```

**File:** `.eslintrc.json`

```json
{
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:react-hooks/recommended",
    "prettier"
  ],
  "parser": "@typescript-eslint/parser",
  "rules": {
    "@typescript-eslint/no-explicit-any": "warn",
    "react-hooks/exhaustive-deps": "warn"
  }
}
```

---

## 📅 1-Week Plan

### Day 1-2: Sprint-10 Integration

**Tasks:**

1. ✅ Add `/engines`, `/backtest`, `/live` API endpoints
2. ✅ Create `/engines` page (engine list + start/stop controls)
3. ✅ Create `/backtest` page (run form + report list)
4. ✅ Update kill switch to new API
5. ✅ Add model card viewer modal

**Files to Create:**

- `src/pages/Engines.tsx`
- `src/pages/Backtest.tsx`
- `src/components/ModelCard.tsx`
- `src/components/BacktestReport.tsx`

### Day 3-4: Testing Infrastructure

**Tasks:**

1. ✅ Setup Vitest + Testing Library
2. ✅ Write API client tests (10+ cases)
3. ✅ Write WebSocket reconnect tests
4. ✅ Write component smoke tests (5 critical pages)
5. ✅ Add CI workflow (GitHub Actions)

**Files to Create:**

- `vitest.config.ts`
- `src/lib/__tests__/api.test.ts`
- `src/lib/__tests__/ws.test.ts`
- `src/pages/__tests__/Overview.test.tsx`
- `.github/workflows/frontend-ci.yml`

### Day 5: Authentication Upgrade

**Tasks:**

1. ✅ Add JWT/refresh token flow
2. ✅ Add auth context provider
3. ✅ Add protected route wrapper
4. ✅ Add session expiry handling
5. ✅ Add logout on 401

**Files to Create:**

- `src/contexts/AuthContext.tsx`
- `src/components/ProtectedRoute.tsx`
- `src/lib/auth.ts`

### Day 6-7: Polish & Documentation

**Tasks:**

1. ✅ Add ESLint + Prettier
2. ✅ Fix all linter errors
3. ✅ Add loading skeletons to all pages
4. ✅ Add error retry UI
5. ✅ Write frontend README
6. ✅ Add Storybook (optional)

**Files to Create:**

- `frontend/panel/README.md`
- `frontend/panel/.eslintrc.json`
- `frontend/panel/.prettierrc.json`

---

## 🚨 Risks & Recommendations

### Critical Risks

| Risk                     | Impact | Mitigation                                 |
| ------------------------ | ------ | ------------------------------------------ |
| **No tests**             | High   | Block production until 50% coverage        |
| **Weak auth**            | High   | Implement JWT + RBAC before public beta    |
| **No error logging**     | Medium | Add Sentry/LogRocket for production        |
| **Missing Sprint-10 UI** | Medium | 2-day sprint to add engines/backtest pages |
| **No CI/CD**             | Medium | Add GitHub Actions for lint + test + build |

### Recommendations

#### Immediate (This Week)

1. **Add Sprint-10 UI** (engines, backtest, kill switch)
2. **Setup basic tests** (Vitest + Testing Library)
3. **Add linting** (ESLint + Prettier)
4. **Create `.env.example`**
5. **Add CI workflow** (lint + test + build)

#### Short-Term (Next Sprint)

1. **Upgrade auth** (JWT + refresh tokens)
2. **Add error logging** (Sentry)
3. **Improve a11y** (ARIA labels, keyboard nav)
4. **Add E2E tests** (Playwright for critical flows)
5. **Performance audit** (React.memo, code splitting)

#### Long-Term (Sprint-11+)

1. **Usage tracking UI** (API key dashboard)
2. **Billing integration** (Stripe checkout)
3. **User management** (RBAC, team invites)
4. **Model marketplace** (browse/buy models)
5. **Mobile responsive** (Tailwind breakpoints)

---

## 📝 Action Items

### For Product Team

- [ ] Prioritize Sprint-10 UI features (engines, backtest, model cards)
- [ ] Define auth requirements (JWT vs session, RBAC roles)
- [ ] Approve Sprint-11 billing/usage tracking designs

### For Engineering Team

- [ ] Implement Sprint-10 API endpoints in frontend (Day 1-2)
- [ ] Setup testing infrastructure (Day 3-4)
- [ ] Add linting + CI (Day 5)
- [ ] Write frontend README (Day 6)

### For DevOps Team

- [ ] Setup frontend CI/CD pipeline (GitHub Actions)
- [ ] Add Sentry project for error logging
- [ ] Configure CDN for static assets (Cloudflare/Vercel)

---

## 🎯 Conclusion

**Current State:** The LeviBot web panel is a **functional prototype** with good architecture (React + Vite + TypeScript + SWR) but **lacks production readiness** (no tests, weak auth, missing Sprint-10 features).

**Recommendation:** Allocate **1 week** to:

1. Add Sprint-10 UI (engines, backtest, kill switch)
2. Setup testing (50% coverage target)
3. Add linting + CI
4. Upgrade auth (JWT + RBAC)

**After 1 week:** Panel will be **production-ready** for Sprint-11 (billing/usage tracking).

**Estimated Effort:** 5-7 days (1 senior frontend engineer)

---

**Audit Complete** ✅  
**Next Steps:** Review with team → Prioritize action items → Execute 1-week plan
