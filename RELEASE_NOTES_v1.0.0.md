# 🚀 LeviBot v1.0.0 — Initial Public Release

**Release Date**: October 2025  
**Codename**: "Full-Stack Altseason Radar"

---

## 🎯 Overview

LeviBot v1.0.0 is a **production-ready, full-stack AI trading suite** that combines:
- 🤖 **ML Signal Scoring** (calibrated confidence)
- 🛡️ **Risk Management** (ATR-based SL/TP, policy-driven)
- 🔐 **Security** (API key auth, rate limiting)
- 📊 **MEV/NFT/L2 Integration** (DEX quotes, NFT floor, L2 yields)
- 🎨 **Admin Panel** (React + Vite, real-time dashboard)
- 📈 **Observability** (Prometheus metrics, JSONL event logging)

**Tech Stack**: FastAPI, React, scikit-learn, CCXT, Telethon, DuckDB, Prometheus

---

## ✨ Key Features

### 🤖 ML Signal Scoring
- **Calibrated Classifier**: `CalibratedClassifierCV` for real 0-1 probabilities
- **Auto-Routing**: ENV-based guards (min confidence, dry-run mode)
- **Channel Trust**: Adjust confidence based on Telegram source reliability
- **Feature Engineering**: Extract TP/SL/Size/Multi-Symbol from text
- **Dataset Pipeline**: CLI tools + Panel UI for adding labeled data
- **Weekly Retrain**: Automated model retraining via cron

### 🛡️ Risk Management
- **ATR-based SL/TP**: Dynamic stop-loss and take-profit based on volatility
- **Risk Policies**: Conservative, Moderate, Aggressive (configurable ATR multipliers)
- **Runtime Policy Switch**: Change policy via API without restart
- **Notional Clamping**: Min/max trade size enforcement
- **Cooldown**: Per-symbol rate limiting to prevent overtrading
- **Hint Priority**: FE-extracted TP/SL overrides ATR calculation

### 🔐 Security
- **API Key Authentication**: Protect sensitive endpoints
- **Rate Limiting**: Sliding-window with burst tolerance
- **PII Masking**: Automatic redaction of sensitive keys in logs
- **Path-based Security**: Configurable secured path prefixes

### 📊 MEV / NFT / L2 Integration
- **DEX Quote**: 0x API integration with offline fallback
- **Tri-Arb Scan**: A→B→C→A arbitrage opportunity detection
- **NFT Floor**: Reservoir API integration with offline fallback
- **NFT Snipe Plan**: Budget + discount calculator
- **L2 Yields**: YAML-based yield tracker (Arbitrum, Base, Optimism)

### 🎨 Admin Panel
- **Dashboard**: Equity chart, controls, trace viewer
- **Trades Page**: Filters (symbol, side), PnL column, pagination
- **Signals Page**: Manual scoring, auto-route preview, policy selector, dataset append
- **Signals Timeline**: Historical scores, auto-routed badges, filters
- **Mini-Cards**: DEX Quote, NFT Floor, L2 Yields (auto-fetch, interactive)

### 📈 Observability
- **Prometheus Metrics**: HTTP requests, latency, events, Telegram health
- **Grafana Dashboards**: Pre-configured panels for monitoring
- **JSONL Event Logging**: Structured, queryable event stream
- **DuckDB Reports**: SQL-based analytics on event logs

---

## 📦 What's Included

### Backend (`backend/`)
- **API** (`src/app/`): FastAPI application with 30+ endpoints
- **Core** (`src/core/`): Risk engine, policy management
- **Signals** (`src/signals/`): ML model, feature engineering, symbol parser
- **Exec** (`src/exec/`): Paper trading, CCXT integration
- **MEV** (`src/mev/`): DEX quote, tri-arb scan
- **NFT** (`src/nft/`): Floor price, snipe plan
- **L2** (`src/l2/`): Yield tracker
- **Infra** (`src/infra/`): Logger, metrics, security middleware
- **Tests** (`tests/`): 32 unit tests (pytest)

### Frontend (`frontend/panel/`)
- **Pages**: Dashboard, Trades, Signals, Signals Timeline
- **Components**: Mini-cards (DEX, NFT, L2), AddToDataset
- **API Client**: Type-safe fetch helpers
- **Styling**: Tailwind CSS, responsive design

### Ops (`ops/`)
- **Prometheus**: Scrape config, alerting rules
- **Grafana**: Dashboard provisioning
- **Docker Compose**: Local monitoring stack
- **Cron**: Weekly model retrain script

### Configs (`backend/configs/`)
- **Features**: Feature flags
- **Risk**: Risk parameters
- **Symbols**: Symbol mappings
- **Telegram**: Channel config
- **Yields**: L2 protocol APRs

---

## 🧪 Testing

**32 unit tests** covering:
- Paper order execution (CCXT + offline)
- Risk engine (cooldown, SL/TP, policies, notional clamping)
- Signal scoring (ML, auto-routing, multi-symbol)
- Feature engineering (TP/SL/Size parser)
- Security (API key auth, rate limiting)
- MEV/NFT/L2 (quote, floor, yields)

**Run tests**:
```bash
PYTHONPATH=/path/to/levibot PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q backend/tests/
# → 32 passed
```

---

## 📊 Metrics & Events

**Prometheus Metrics**:
- `levibot_http_requests_total` (counter)
- `levibot_http_request_latency_seconds` (histogram)
- `levibot_events_total` (counter by event_type)
- `levibot_tg_reconnects_total` (counter)
- `levibot_tg_last_message_ts` (gauge)

**Event Types** (40+):
- `ORDER_NEW`, `ORDER_FILLED`, `POSITION_CLOSED`
- `SIGNAL_SCORED`, `AUTO_ROUTE_EXECUTED`, `AUTO_ROUTE_SKIPPED`
- `RISK_SLTP`, `RISK_POLICY_CHANGED`, `ORDER_BLOCKED`
- `DEX_QUOTE`, `MEV_TRI`, `NFT_FLOOR`, `L2_YIELDS`
- `DS_APPEND`, `TG_MESSAGE`, `TG_RECONNECT`

---

## 🚀 Quick Start

### 1. Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ENV.example .env
# Edit .env with your API keys
uvicorn src.app.main:app --reload
# → http://localhost:8000
```

### 2. Frontend
```bash
cd frontend/panel
npm install
npm run dev
# → http://localhost:5173
```

### 3. Monitoring (Optional)
```bash
cd ops
docker-compose up -d
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin)
```

---

## 🔧 Configuration

**Key ENV Variables**:
```bash
# Auto-Routing
AUTO_ROUTE_ENABLED=true
AUTO_ROUTE_DRY_RUN=false
AUTO_ROUTE_MIN_CONF=0.75
AUTO_ROUTE_DEFAULT_NOTIONAL=25

# Risk Policy
RISK_POLICY=moderate  # conservative | moderate | aggressive
RISK_MIN_NOTIONAL=5
RISK_MAX_NOTIONAL=250

# Security
API_KEYS=your-secret-key
RATE_LIMIT_WINDOW_SEC=60
RATE_LIMIT_MAX=120
SECURED_PATH_PREFIXES=/signals,/exec,/paper

# MEV / NFT
ZEROX_API_KEY=
RESERVOIR_API_KEY=

# Telegram
TELEGRAM_API_ID=
TELEGRAM_API_HASH=
TELEGRAM_CHANNELS=channel1,channel2
```

---

## 📚 Documentation

- **README.md**: Comprehensive setup guide, API reference, troubleshooting
- **ENV.example**: All environment variables with descriptions
- **docs/**: Architecture, design decisions, deployment guides

---

## 🎯 Use Cases

1. **Paper Trading Bot**: Auto-route Telegram signals to paper orders
2. **Signal Research**: Score historical messages, build dataset, retrain model
3. **Risk Backtesting**: Test different policies on historical trades
4. **MEV Monitoring**: Track DEX arbitrage opportunities
5. **NFT Sniping**: Monitor floor prices, calculate snipe targets
6. **L2 Yield Farming**: Track protocol APRs across chains

---

## 🔮 Roadmap (v1.1+)

- [ ] **Live Trading**: Binance/Bybit execution (currently paper-only)
- [ ] **Redis Rate Limit**: Distributed rate limiting for multi-instance
- [ ] **Panel Charts**: DEX price history, L2 yield trends
- [ ] **Webhook Integration**: Discord/Slack notifications
- [ ] **Backtesting Engine**: Historical signal replay with P&L
- [ ] **Multi-Model Ensemble**: Combine multiple ML models
- [ ] **Real-time WebSocket**: Live signal feed in Panel

---

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/) + [Vite](https://vitejs.dev/)
- [scikit-learn](https://scikit-learn.org/)
- [CCXT](https://github.com/ccxt/ccxt)
- [Telethon](https://github.com/LonamiWebs/Telethon)
- [Prometheus](https://prometheus.io/)
- [DuckDB](https://duckdb.org/)

---

## 📄 License

MIT License — see `LICENSE` file for details.

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📧 Contact

- **Issues**: [GitHub Issues](https://github.com/yourusername/levibot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/levibot/discussions)

---

**🚀 Happy Trading!**
