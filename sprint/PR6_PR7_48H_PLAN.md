# 🗓️ 48-Hour Execution Plan: PR-6 & PR-7

**Start:** October 14, 2025 (T+0)  
**End:** October 16, 2025 (T+48h)  
**Goal:** Production-ready frontend (Lint + Tests + Auth + 48h Paper Trading)

---

## 📊 Timeline Overview

```
T+0h  ────────────── T+12h ────────────── T+24h ────────────── T+36h ────────────── T+48h
│                    │                    │                    │                    │
├─ Quick Smoke       ├─ PR-6 Complete     ├─ PR-7 Complete     ├─ Paper Trade      ├─ Ops Report
│  Bug-Bash          │  (Lint+Tests+CI)   │  (JWT+RBAC)        │  24h Monitor       │  Demo Ready
│                    │                    │                    │                    │
└─ 5min smoke        └─ CI green ✅       └─ Auth working ✅   └─ Mid checkpoint   └─ Final review
   15min bug-bash       coverage 50%+        JWT + refresh         p95 < 50ms         All systems go
```

---

## 🔎 Phase 1: Quick Smoke + Bug-Bash (T+0 → T+2h)

### Quick Smoke (5 min)

**File:** `frontend/panel/QUICK_SMOKE.md`

**Tasks:**
1. ✅ Start backend + frontend
2. ✅ Test `/engines` (SSE + Start/Stop)
3. ✅ Test `/backtest` (Run + Reports)
4. ✅ Test `/ops` (Kill Switch)

**Output:** Smoke test status (Pass/Fail)

---

### Mini Bug-Bash (15 min)

**File:** `frontend/panel/BUG_BASH_CHECKLIST.md`

**6 Scenarios:**
1. Error Handling (backend down, timeout, 404/500)
2. SSE Reconnection (2s backoff, exponential retry)
3. Environment & Fallbacks (missing .env, invalid API base)
4. Dark Mode Accessibility (WCAG AA contrast)
5. Empty States (no engines, no reports)
6. Optimistic UI (disabled buttons, loading states)

**Output:** Bug list (critical/high/medium/low)

---

### Quick Fixes (1.5 h)

**Priorities:**
- Fix critical bugs (blockers)
- Fix high-priority bugs (must-have)
- Document medium/low bugs for PR-6

**Commit:** `fix(frontend): Critical bug fixes from bug-bash`

---

## 🔧 Phase 2: PR-6 - Linting + Testing + CI (T+2h → T+14h)

### Task 1: ESLint + Prettier Setup (1h)

**Dependencies:**
```bash
cd /Users/onur/levibot/frontend/panel
pnpm add -D eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin
pnpm add -D prettier eslint-config-prettier eslint-plugin-react-hooks
pnpm add -D eslint-plugin-react eslint-plugin-react-refresh
```

**Files to Create:**
- `.eslintrc.json` - ESLint config (TypeScript + React)
- `.prettierrc.json` - Prettier config (2 spaces, single quotes)
- `.eslintignore` - Ignore patterns (dist, node_modules)

**Config:**
```json
// .eslintrc.json
{
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:react-hooks/recommended",
    "plugin:react/recommended",
    "prettier"
  ],
  "parser": "@typescript-eslint/parser",
  "parserOptions": {
    "ecmaVersion": "latest",
    "sourceType": "module",
    "ecmaFeatures": { "jsx": true }
  },
  "rules": {
    "@typescript-eslint/no-explicit-any": "warn",
    "@typescript-eslint/no-unused-vars": ["warn", { "argsIgnorePattern": "^_" }],
    "react-hooks/exhaustive-deps": "warn",
    "react/react-in-jsx-scope": "off"
  },
  "settings": {
    "react": { "version": "detect" }
  }
}
```

**Scripts (package.json):**
```json
"scripts": {
  "lint": "eslint src --ext .ts,.tsx",
  "lint:fix": "eslint src --ext .ts,.tsx --fix",
  "format": "prettier --write \"src/**/*.{ts,tsx,css}\"",
  "format:check": "prettier --check \"src/**/*.{ts,tsx,css}\""
}
```

**Run:**
```bash
pnpm lint:fix
pnpm format
```

**Commit:** `chore(frontend): Add ESLint + Prettier config`

---

### Task 2: Vitest + Testing Library Setup (1.5h)

**Dependencies:**
```bash
pnpm add -D vitest @vitest/ui jsdom
pnpm add -D @testing-library/react @testing-library/jest-dom @testing-library/user-event
pnpm add -D @types/node
```

**Files to Create:**
- `vitest.config.ts` - Vitest config (jsdom, coverage)
- `src/test/setup.ts` - Test setup (@testing-library/jest-dom)

**Config:**
```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: ['node_modules/', 'src/test/']
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
})
```

**Scripts (package.json):**
```json
"scripts": {
  "test": "vitest",
  "test:ui": "vitest --ui",
  "test:coverage": "vitest --coverage"
}
```

**Commit:** `chore(frontend): Add Vitest + Testing Library`

---

### Task 3: Write Tests (6h)

**API Client Tests** (`src/lib/__tests__/api.test.ts`):
- `http()` success (200)
- `http()` error (404, 500)
- `http()` network error (timeout)
- `api.engines.list()` returns array
- `api.engines.start()` sends POST
- `api.backtest.run()` sends params
- `api.live.kill()` sends body
- `api.models.cards()` returns LGBM + TFT

**SSE Tests** (`src/lib/__tests__/sse.test.ts`):
- `openSSE()` connects successfully
- `openSSE()` parses JSON messages
- `openSSE()` reconnects after error (2s delay)
- `openSSE()` cleanup closes connection

**Component Tests** (`src/pages/__tests__/`):
- `EnginesManager.test.tsx` - Renders table, start/stop buttons
- `BacktestRunner.test.tsx` - Renders form, run button
- `Ops.test.tsx` - Kill switch toggle

**Target Coverage:** ≥50% (line coverage)

**Commit:** `test(frontend): Add API, SSE, and component tests`

---

### Task 4: GitHub Actions CI (2h)

**File:** `.github/workflows/frontend-ci.yml`

**Config:**
```yaml
name: Frontend CI

on:
  push:
    branches: [main, develop]
    paths:
      - 'frontend/panel/**'
  pull_request:
    branches: [main, develop]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: pnpm/action-setup@v2
        with:
          version: 8
      
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'pnpm'
          cache-dependency-path: frontend/panel/pnpm-lock.yaml
      
      - name: Install dependencies
        working-directory: frontend/panel
        run: pnpm install --frozen-lockfile
      
      - name: Lint
        working-directory: frontend/panel
        run: pnpm lint
      
      - name: Format check
        working-directory: frontend/panel
        run: pnpm format:check
      
      - name: Test
        working-directory: frontend/panel
        run: pnpm test:coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: frontend/panel/coverage/coverage-final.json
      
      - name: Build
        working-directory: frontend/panel
        run: pnpm build
```

**Commit:** `ci(frontend): Add GitHub Actions workflow`

---

### Task 5: Fix Lint/Test Issues (2.5h)

**Tasks:**
- Fix all ESLint warnings (no `any`, unused vars)
- Fix all Prettier formatting issues
- Fix failing tests (mocks, async handlers)
- Achieve ≥50% coverage

**Commit:** `fix(frontend): Resolve lint and test issues`

---

**Phase 2 Output:**
- ✅ ESLint + Prettier configured
- ✅ Vitest + Testing Library setup
- ✅ 10+ tests passing
- ✅ Coverage ≥50%
- ✅ GitHub Actions CI passing

---

## 🔒 Phase 3: PR-7 - Auth Upgrade (JWT + RBAC) (T+14h → T+26h)

### Task 1: Backend JWT Endpoints (2h)

**Skip if already exists**, otherwise:

**Files:**
- `backend/src/auth/jwt.py` - JWT token generation + validation
- `backend/src/app/routers/auth.py` - `/auth/login`, `/auth/refresh`

**Endpoints:**
- `POST /auth/login` - Email + password → JWT + refresh token
- `POST /auth/refresh` - Refresh token → New JWT
- `POST /auth/logout` - Invalidate refresh token

---

### Task 2: Frontend Auth Context (3h)

**Files to Create:**
- `src/contexts/AuthContext.tsx` - Auth state + login/logout
- `src/components/ProtectedRoute.tsx` - Route guard
- `src/lib/auth.ts` - JWT decode, token refresh

**Auth Context:**
```typescript
// src/contexts/AuthContext.tsx
import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { api } from '@/lib/api';

type User = { id: string; email: string; role: 'viewer' | 'admin' };
type AuthContextType = {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
};

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing session
    const token = localStorage.getItem('jwt');
    if (token) {
      // Decode and validate token
      // If valid, setUser(); else logout()
    }
    setLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    const res = await api.auth.login(email, password);
    localStorage.setItem('jwt', res.access_token);
    localStorage.setItem('refresh_token', res.refresh_token);
    setUser(res.user);
  };

  const logout = () => {
    localStorage.removeItem('jwt');
    localStorage.removeItem('refresh_token');
    setUser(null);
  };

  if (loading) return <div>Loading...</div>;

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};
```

**Protected Route:**
```typescript
// src/components/ProtectedRoute.tsx
import { Navigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';

export function ProtectedRoute({ children, requireAdmin }: { children: ReactNode; requireAdmin?: boolean }) {
  const { user, isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (requireAdmin && user?.role !== 'admin') {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
```

---

### Task 3: Login Page (2h)

**File:** `src/pages/Login.tsx`

**Features:**
- Email + password form
- Error handling (invalid credentials)
- Remember me checkbox (optional)
- Redirect to original page after login

---

### Task 4: Integrate Auth (2h)

**Updates:**
- `src/App.tsx` - Wrap with `<AuthProvider>`
- `src/App.tsx` - Wrap protected routes with `<ProtectedRoute>`
- `src/lib/api.ts` - Add JWT header (`Authorization: Bearer <token>`)
- `src/lib/api.ts` - Auto-refresh on 401

**Example:**
```typescript
// src/lib/api.ts
export async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const token = localStorage.getItem('jwt');
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
    ...(init?.headers || {})
  };

  let res = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    ...init,
    headers
  });

  // Auto-refresh on 401
  if (res.status === 401) {
    const refreshed = await refreshToken();
    if (refreshed) {
      // Retry request with new token
      res = await fetch(`${API_BASE}${path}`, {
        credentials: 'include',
        ...init,
        headers: { ...headers, Authorization: `Bearer ${localStorage.getItem('jwt')}` }
      });
    } else {
      // Redirect to login
      window.location.href = '/login';
      throw new Error('Session expired');
    }
  }

  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return await res.json() as T;
}
```

---

### Task 5: RBAC - Role-Based Actions (2h)

**Features:**
- `viewer` role: Read-only (can view engines, backtest reports)
- `admin` role: Full access (can start/stop engines, run backtests, kill switch)

**Implementation:**
- Disable buttons for `viewer` role
- Show tooltips ("Admin only")
- Hide admin-only sections

**Example:**
```typescript
// src/pages/EnginesManager.tsx
const { user } = useAuth();
const isAdmin = user?.role === 'admin';

<button
  disabled={!isAdmin || busy === engine.symbol}
  onClick={() => handleAction('start', engine.symbol)}
  title={!isAdmin ? 'Admin only' : undefined}
>
  Start
</button>
```

---

### Task 6: Session Management (2h)

**Features:**
- Auto-logout on token expiry (7 days for refresh token)
- Auto-refresh JWT before expiry (e.g., every 50 min if expires in 60 min)
- Show session timeout warning (5 min before expiry)

**Implementation:**
- `useEffect` hook in `AuthContext`
- `setInterval` for token refresh
- Toast notification for timeout warning

---

**Phase 3 Output:**
- ✅ JWT auth working (login, logout, refresh)
- ✅ Protected routes (redirect to /login)
- ✅ RBAC (viewer vs admin)
- ✅ Session management (auto-refresh, timeout warning)
- ✅ Auth tests passing

---

## 📊 Phase 4: 48h Paper Trading Monitor (T+26h → T+48h)

### Setup Paper Trading (1h)

**Backend:**
```bash
# Set paper mode in backend/src/app/main.py
engines_config = {
  "mode": "paper",  # Not "real"
  "symbols": ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
}
```

**Frontend:**
- Navigate to `/engines`
- Start all engines
- Verify "Paper" mode badge visible

---

### 24h Monitoring (T+26h → T+38h)

**Checkpoints:**
- **T+27h** (1h after start): Engines running? No crashes?
- **T+30h** (4h): First trades executed? PnL tracking?
- **T+32h** (6h): SSE still connected? Metrics updating?
- **T+34h** (8h): Any errors in logs? p95 latency < 50ms?
- **T+38h** (12h): Mid-checkpoint report

**Mid-Checkpoint Report:**
```markdown
# 24h Paper Trading - Mid Checkpoint

**Time:** T+38h (12h into paper trading)

**Engines Status:**
- BTC/USDT: ✅ Running (12h uptime, 15 trades, +2.3% PnL)
- ETH/USDT: ✅ Running (12h uptime, 22 trades, +1.8% PnL)
- SOL/USDT: ⚠️ Degraded (1 error at T+30h, recovered)

**Metrics:**
- p95 Latency: 45ms (< 50ms target ✅)
- Error Rate: 0.05% (< 0.1% target ✅)
- SSE Uptime: 100% (no disconnects ✅)
- Queue p95: 8 (< 32 target ✅)

**Issues:**
- None critical
- 1 minor: SOL/USDT error (timeout on backfill)

**Actions:**
- Continue monitoring
- Next checkpoint: T+48h
```

---

### 48h Final Report (T+48h)

**Metrics to Collect:**
- Total trades per symbol
- PnL per symbol (paper)
- p95 inference latency
- Error rate
- SSE uptime
- Kill switch tests (manual + auto triggers)

**Final Report:**
```markdown
# 48h Paper Trading - Final Report

**Time:** T+48h (48h uptime)

**Summary:**
- ✅ All engines stable (48h continuous operation)
- ✅ Metrics within targets (p95 < 50ms, error < 0.1%)
- ✅ SSE reconnection working (tested 3 intentional disconnects)
- ✅ Kill switch working (tested manual + auto triggers)
- ✅ Auth working (JWT + RBAC tested)

**Detailed Metrics:**
[See full table...]

**Known Issues:**
[List any minor issues...]

**Recommendations:**
[Next steps for production...]
```

---

## ✅ Definition of Done (T+48h)

**PR-6 (Lint + Tests + CI):**
- ✅ ESLint + Prettier configured and passing
- ✅ Vitest + Testing Library setup
- ✅ 10+ tests passing (API, SSE, components)
- ✅ Coverage ≥50%
- ✅ GitHub Actions CI green
- ✅ All lint errors fixed
- ✅ All format issues fixed

**PR-7 (Auth):**
- ✅ JWT login/logout/refresh working
- ✅ Protected routes redirect to /login
- ✅ RBAC (viewer vs admin) enforced
- ✅ Session management (auto-refresh, timeout)
- ✅ Auth tests passing
- ✅ No localStorage leaks (clear on logout)

**48h Paper Trading:**
- ✅ 48h continuous operation (no crashes)
- ✅ Metrics within targets (p95, error rate, uptime)
- ✅ SSE reconnection tested and working
- ✅ Kill switch tested (manual + auto)
- ✅ Final report published

**Demo Ready:**
- ✅ All pages load without errors
- ✅ All features working (engines, backtest, kill switch)
- ✅ Auth working (login, RBAC)
- ✅ Dark mode working
- ✅ Documentation updated (README, guides)

---

## 📝 Deliverables

**Files Created/Updated:**
1. `frontend/panel/.eslintrc.json` - ESLint config
2. `frontend/panel/.prettierrc.json` - Prettier config
3. `frontend/panel/vitest.config.ts` - Vitest config
4. `frontend/panel/src/lib/__tests__/*.test.ts` - Tests
5. `frontend/panel/src/contexts/AuthContext.tsx` - Auth state
6. `frontend/panel/src/components/ProtectedRoute.tsx` - Route guard
7. `frontend/panel/src/pages/Login.tsx` - Login page
8. `.github/workflows/frontend-ci.yml` - CI workflow
9. `sprint/48H_PAPER_TRADING_REPORT.md` - Final report

**Documentation:**
- `frontend/panel/README.md` - Updated with lint/test commands
- `sprint/PR6_COMPLETION.md` - PR-6 summary
- `sprint/PR7_COMPLETION.md` - PR-7 summary

---

## 🚀 Next Steps After T+48h

**Sprint-11 Kickoff:**
- Usage tracking (API key dashboard)
- Billing integration (Stripe placeholder)
- User management (team invites)
- Model marketplace (browse/buy models)

**Production Deployment:**
- Real MEXC API integration (HMAC signing)
- Prometheus + Grafana dashboards
- Alerts (PagerDuty/Slack)
- Backup & recovery procedures

---

**Timeline Complete** ✅  
**All systems production-ready** 🚀  
**Sprint-10 → Sprint-11 transition smooth** 🎯

