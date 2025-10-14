# 🚀 LeviBot v1.1.0 — Production-ready Stack

**Release Date**: October 2025  
**Codename**: "Sprint 4 — Redis, Charts, Docker"

---

## 🎯 What's New

### PR-21: Redis-backed Distributed Rate Limit
- **Token bucket** algorithm with Lua script (atomic ops)
- **Graceful fallback** to in-memory when Redis unavailable
- **Distributed-ready** for multi-instance deployments
- 3 unit tests (fallback + redis path + enforcement)

### PR-22: Panel Mini-Charts
- **DEX Sparkline**: 24-point timeseries, 30s auto-refresh
- **L2 Yields Bar**: Protocol APR comparison chart
- **Recharts** integration, responsive design
- Auto-refresh with manual override

### PR-23: Docker Production Compose
- **Single command deploy**: `make prod-up`
- **Full stack**: Redis + API + Panel + Nginx
- **Health checks**: Service dependencies, restart policies
- **Multi-stage builds**: Optimized image sizes
- **Production-ready**: Persistent volumes, reverse proxy

---

## 📊 Stats

- **38 backend tests** (35 from v1.0.0 + 3 new)
- **9 major features**
- **8 frontend components**
- **Production-ready + Demo-ready + Deploy-ready**

---

## 🚀 Quick Start (Docker)

```bash
# 1) Clone repo
git clone https://github.com/siyahkare/levibot.git
cd levibot

# 2) Setup ENV
cp .env.prod.example .env.prod
# Edit: API_KEYS, optional ZEROX_API_KEY, RESERVOIR_API_KEY

# 3) Deploy
make prod-up

# 4) Verify
curl -s http://localhost/healthz | jq
open http://localhost
```

---

## 📦 What's Included

### Backend
- Redis-backed rate limiting
- Risk++ (ATR-based SL/TP, policies)
- Feature Engineering (TP/SL/Size, multi-symbol)
- MEV/NFT/L2 integration
- Security (API key auth, rate limit)

### Frontend
- Mini-cards (DEX Quote, NFT Floor, L2 Yields)
- Mini-charts (DEX Sparkline, L2 Bar)
- Signals scoring + timeline
- Auto-refresh (30s interval)

### Ops
- Docker Compose (prod-ready)
- Nginx reverse proxy
- Health checks + restart policies
- GitHub Actions CI

---

## 🔗 Links

- **Documentation**: [README.md](https://github.com/siyahkare/levibot/blob/main/README.md)
- **v1.0.0 Release Notes**: [RELEASE_NOTES_v1.0.0.md](https://github.com/siyahkare/levibot/blob/main/RELEASE_NOTES_v1.0.0.md)
- **Issues**: [GitHub Issues](https://github.com/siyahkare/levibot/issues)

---

**🚀 Happy Trading!**
