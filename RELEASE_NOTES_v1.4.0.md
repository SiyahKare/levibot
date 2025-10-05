# LeviBot v1.4.0 — Docs & Developer Experience

**Date:** 2025-10-05  
**Codename:** Sprint 7 — Docs & Polish

## 📚 What's new

### PR-29 · GitHub Templates & Contributing
- Issue templates (bug/feature) with structured YAML forms
- Comprehensive PR template with checklist
- `CONTRIBUTING.md` with branch naming, commit style, PR flow, and testing guidelines

### PR-30 · Architecture & Deployment Docs
- `docs/ARCHITECTURE.md` with Mermaid component diagrams and request flows
- `docs/DEPLOYMENT.md` with production deployment guide (Docker Compose, Nginx, Redis, S3)

### PR-31 · Performance Baseline
- `pytest-benchmark` integration for performance regression tracking
- `docs/PERFORMANCE.md` with benchmarking methodology
- Makefile targets: `make perf`, `make perf-save`, `make perf-compare`
- Baseline metrics for `/readyz`, `/signals/score`, `/dex/quote`

### PR-32 · Security Checklist
- `SECURITY.md` with vulnerability reporting policy, SLA targets, and supported versions
- `.github/dependabot.yml` for automated weekly dependency updates (pip, npm, actions)
- `.github/workflows/security.yml` with CodeQL (Python & JavaScript) and Bandit (Python SAST)
- Security scan badge in README

### PR-33 · Developer Experience
- `.editorconfig` for consistent code style across editors
- `.vscode/settings.json` with recommended VS Code settings (format on save, pytest, ruff)
- `.vscode/extensions.json` with recommended extensions (Python, Ruff, Docker, Prettier, ESLint)
- `.ruff.toml` linter configuration (line-length 100, Python 3.11+)
- Makefile developer helpers:
  - `make fmt` — Format Python code (black + ruff imports)
  - `make lint` — Lint Python + Frontend
  - `make clean` — Remove cache files
  - `make fix-frontend` — Auto-fix frontend (prettier + eslint)

## 🔒 Security & Quality

- **SAST Scanning**: CodeQL + Bandit weekly scans on push/PR/schedule
- **Dependency Management**: Dependabot weekly updates with security patch grouping
- **Performance Tracking**: Benchmark baselines for p50/p90/p99 latency
- **Vulnerability SLA**:
  - First response: 2 business days
  - Initial assessment: 5 business days
  - Fix & release: 14 days (critical), 30 days (high)

## 🔧 Developer Experience

- **Consistent Environment**: EditorConfig + VS Code settings for unified dev experience
- **One-command Workflows**: Format, lint, clean, and fix with single make commands
- **Standardized Contributions**: GitHub templates for issues and PRs
- **Fast Onboarding**: Architecture docs + recommended extensions + CONTRIBUTING guide

## 🧯 Breaking Changes

**None.** v1.4.0 is fully compatible with v1.3.x.

## 📝 Upgrade Notes

1. **Optional**: Install recommended VS Code extensions (prompt on first open)
2. **Verify**: Run `make fmt && make lint` for local validation
3. **Review**: Check `CONTRIBUTING.md` for updated PR flow
4. **Security**: Review `SECURITY.md` for vulnerability reporting process

## 📊 Release Matrix

| Feature | Status | Docs |
|---------|--------|------|
| GitHub Templates | ✅ | `.github/ISSUE_TEMPLATE/*`, `.github/PULL_REQUEST_TEMPLATE.md` |
| Architecture Docs | ✅ | `docs/ARCHITECTURE.md` |
| Deployment Guide | ✅ | `docs/DEPLOYMENT.md` |
| Performance Baseline | ✅ | `docs/PERFORMANCE.md`, `backend/tests/test_performance.py` |
| Security Policy | ✅ | `SECURITY.md`, `.github/workflows/security.yml` |
| Developer Tools | ✅ | `.editorconfig`, `.vscode/*`, `.ruff.toml`, `Makefile` |
| Dependabot | ✅ | `.github/dependabot.yml` |
| SAST Scans | ✅ | CodeQL (Python/JS), Bandit (Python) |

## 🎯 Sprint 7 Highlights

- **18 files changed**, +1,400 lines
- **5 PRs** merged (PR-29 to PR-33)
- **4 new docs** (Architecture, Deployment, Performance, Security)
- **3 GitHub workflows** (CI, Security, Dependabot)
- **Community-ready**: Open source contribution infrastructure complete

## 🙏 Contributors

- @onur (Sprint 7 lead)

## 🔗 Links

- **Full Changelog**: https://github.com/SiyahKare/levibot/compare/v1.3.0...v1.4.0
- **Documentation**: https://github.com/SiyahKare/levibot/tree/main/docs
- **Security Policy**: https://github.com/SiyahKare/levibot/security/policy
- **Contributing Guide**: https://github.com/SiyahKare/levibot/blob/main/CONTRIBUTING.md

---

**Next up:** Sprint 8 — Webhook Triggers / Alerting / GraphQL 🚀
