# 📚 LeviBot Planlama Dokümanları - İndeks

**Oluşturulma:** 13 Ekim 2025  
**Proje:** LeviBot v1.6.1 → v2.0 Strategic Planning

---

## 🎯 Doküman Hiyerarşisi

```
docs/PLANNING_INDEX.md (bu dosya)
│
├─📊 Stratejik Seviye (C-Level, Investor)
│  └── ./DEVELOPMENT_PLAN_SUMMARY.md     ← Executive summary (5 dakika okuma)
│
├─📋 Taktik Seviye (Product/Engineering Manager)
│  ├── DEVELOPMENT_ROADMAP.md          ← Detaylı 12 aylık plan (30 dakika)
│  └── TECHNICAL_EVOLUTION.md          ← Teknik mimari evrim (20 dakika)
│
└─⚙️ Operasyonel Seviye (Developer, DevOps)
   ├── ./SPRINT_PLANNING.md              ← Sprint execution guide (15 dakika)
   ├── GO_LIVE_PLAYBOOK.md             ← Production runbook (10 dakika)
   └── ML_SPRINT3_GUIDE.md             ← ML ops guide (10 dakika)
```

---

## 📖 Kılavuz: Hangi Dokümanı Ne Zaman Okumalı?

### Rol: CEO / Founder

**Hedef:** Yüksek seviye vizyon, bütçe, timeline

1. **İlk okuma:** [./DEVELOPMENT_PLAN_SUMMARY.md](./DEVELOPMENT_PLAN_SUMMARY.md)

   - KPI'lar, finansal projeksiyon, risk analizi
   - **Süre:** 5 dakika
   - **Aksiyon:** Go/no-go kararı, bütçe onayı

2. **Detaylı review:** [./DEVELOPMENT_ROADMAP.md](./DEVELOPMENT_ROADMAP.md)
   - Sprint-by-sprint breakdown
   - **Süre:** 30 dakika (quarterly review'da)
   - **Aksiyon:** Önceliklendirme, kaynak tahsisi

### Rol: CTO / Tech Lead

**Hedef:** Teknik strateji, mimari kararlar

1. **İlk okuma:** [./DEVELOPMENT_PLAN_SUMMARY.md](./DEVELOPMENT_PLAN_SUMMARY.md)

   - Teknik KPI'lar, teknoloji borçları
   - **Süre:** 5 dakika

2. **Detaylı okuma:** [./DEVELOPMENT_ROADMAP.md](./DEVELOPMENT_ROADMAP.md)

   - Sprint planning, team capacity
   - **Süre:** 30 dakika

3. **Mimari planning:** [./TECHNICAL_EVOLUTION.md](./TECHNICAL_EVOLUTION.md)
   - Microservice migration, K8s, database strategy
   - **Süre:** 20 dakika
   - **Aksiyon:** Mimari kararlar, PoC'ler

### Rol: Product Manager

**Hedef:** Feature roadmap, user value

1. **İlk okuma:** [./DEVELOPMENT_PLAN_SUMMARY.md](./DEVELOPMENT_PLAN_SUMMARY.md)

   - Feature list, milestone'lar, success metrics
   - **Süre:** 5 dakika

2. **Sprint planning:** [./SPRINT_PLANNING.md](./SPRINT_PLANNING.md)
   - User story'ler, acceptance criteria
   - **Süre:** 15 dakika (her sprint başı)
   - **Aksiyon:** Backlog grooming, prioritization

### Rol: Backend Developer

**Hedef:** Günlük implementation, sprint tasks

1. **İlk okuma:** [./SPRINT_PLANNING.md](./SPRINT_PLANNING.md)

   - Story breakdown, technical tasks, DoD
   - **Süre:** 15 dakika
   - **Aksiyon:** Günlük standup, task pickup

2. **Context için:** [./DEVELOPMENT_ROADMAP.md](./DEVELOPMENT_ROADMAP.md)

   - Uzun vadeli plan (big picture)
   - **Süre:** 30 dakika (opsiyonel)

3. **Deployment için:** [./GO_LIVE_PLAYBOOK.md](./GO_LIVE_PLAYBOOK.md)
   - Production deployment, health checks
   - **Süre:** 10 dakika
   - **Aksiyon:** Deploy checklist

### Rol: ML Engineer

**Hedef:** Model training, experimentation

1. **İlk okuma:** [./ML_SPRINT3_GUIDE.md](./ML_SPRINT3_GUIDE.md)

   - Drift detection, canary deployment, shadow mode
   - **Süre:** 10 dakika

2. **Sprint tasks:** [./SPRINT_PLANNING.md](./SPRINT_PLANNING.md)

   - Sprint 10 (AI/ML epic'leri)
   - **Süre:** 15 dakika

3. **Uzun vadeli:** [./DEVELOPMENT_ROADMAP.md](./DEVELOPMENT_ROADMAP.md)
   - Advanced AI layer, RL, AutoML
   - **Süre:** 30 dakika

### Rol: DevOps / SRE

**Hedef:** Infrastructure, monitoring, reliability

1. **İlk okuma:** [./GO_LIVE_PLAYBOOK.md](./GO_LIVE_PLAYBOOK.md)

   - Validation, monitoring, incident runbook
   - **Süre:** 10 dakika

2. **Infrastructure plan:** [./TECHNICAL_EVOLUTION.md](./TECHNICAL_EVOLUTION.md)

   - K8s migration, database scaling, multi-region
   - **Süre:** 20 dakika

3. **Sprint tasks:** [./SPRINT_PLANNING.md](./SPRINT_PLANNING.md)
   - Sprint 9 (production hardening)
   - **Süre:** 15 dakika

---

## 🎯 Doküman Özeti (TL;DR)

### 1. ./DEVELOPMENT_PLAN_SUMMARY.md (5 dk)

**Özet:** Yönetici özeti - KPI, finansal, risk, öncelikler  
**Hedef Kitle:** CEO, Board, Investor  
**Anahtar İçerik:**

- Mevcut durum snapshot
- 12 aylık hedefler (3-6-12 ay)
- Öncelikli sprint'ler (9, 10, 11, 12)
- Finansal projeksiyon ($500 → $25K MRR)
- Kilometre taşları (6 milestone)

**Aksiyon Öğeleri:**

- [ ] Bütçe onayı ($2,300/mo → $7,940/mo)
- [ ] Hiring plan (1-2 developer)
- [ ] Go/no-go kararı

---

### 2. ./DEVELOPMENT_ROADMAP.md (30 dk)

**Özet:** Detaylı 12 aylık plan - Sprint breakdown, KPI, risk analizi  
**Hedef Kitle:** CTO, Product Manager, Tech Lead  
**Anahtar İçerik:**

- Sprint 9-14 detaylı breakdown
- Epic'ler, story'ler, acceptance criteria
- Teknik borçlar (10+ item)
- Risk register (15+ risk)
- Öğrenme hedefleri

**Aksiyon Öğeleri:**

- [ ] Sprint capacity planning
- [ ] Team upskilling (CKA, Go, distributed systems)
- [ ] Quarterly OKR set

---

### 3. ./TECHNICAL_EVOLUTION.md (20 dk)

**Özet:** Mimari evrim - Monolith → Microservices, K8s migration  
**Hedef Kitle:** CTO, Tech Lead, DevOps  
**Anahtar İçerik:**

- Current vs target architecture
- 6-month migration roadmap (strangler fig pattern)
- Database evolution (TimescaleDB, ClickHouse cluster)
- Security enhancements (OAuth2, mTLS, secrets)
- Multi-region strategy (active-passive → active-active)
- Cost estimation ($72/mo → $7,940/mo)

**Aksiyon Öğeleri:**

- [ ] Service boundary POC (ML Service first)
- [ ] K8s cluster setup (EKS/GKE)
- [ ] IaC setup (Terraform)

---

### 4. ./SPRINT_PLANNING.md (15 dk)

**Özet:** Sprint execution guide - Story templates, DoD, retrospective  
**Hedef Kitle:** Developer, Scrum Master  
**Anahtar İçerik:**

- Sprint template (planning → review → retro)
- Sprint 9 & 10 detailed stories (40-60 SP)
- User story format (As a X, I want Y, So that Z)
- Technical tasks, verification steps
- Quality gates (pre-merge, pre-deploy, post-deploy)

**Aksiyon Öğeleri:**

- [ ] Sprint kick-off meeting
- [ ] Daily standup (async Slack)
- [ ] Code review, testing, deploy

---

### 5. ./GO_LIVE_PLAYBOOK.md (10 dk)

**Özet:** Production runbook - Validation, monitoring, incident response  
**Hedef Kitle:** DevOps, SRE, Developer  
**Anahtar İçerik:**

- 3 deployment paths (DB'siz fallback, DB'li real model, Canary)
- Validation checklist (health check, prod-ready script)
- Monitoring (Prometheus metrics, Grafana dashboards)
- Incident runbook (data stale, model issue, kill switch)
- Daily ops commands (Makefile shortcuts)

**Aksiyon Öğeleri:**

- [ ] Run `make prod-ready`
- [ ] Setup cron (health check every 5 min)
- [ ] Configure alerts (PagerDuty, Slack)

---

### 6. ./ML_SPRINT3_GUIDE.md (10 dk)

**Özet:** ML ops guide - Drift detection, canary, shadow mode  
**Hedef Kitle:** ML Engineer, Data Scientist  
**Anahtar İçerik:**

- Drift detection (PSI, KS test)
- Canary deployment (10% traffic, auto-promote)
- Ensemble auto-tuner (Sharpe-optimized weights)
- Shadow logging (predictions + trades)
- Go-live checklist (10 min validation)

**Aksiyon Öğeleri:**

- [ ] Run `bash backend/scripts/go_live_checklist.sh`
- [ ] Setup cron (drift check every 15 min)
- [ ] Enable shadow mode

---

## 🔄 Doküman Güncelleme Döngüsü

| Doküman                       | Güncelleme Sıklığı   | Sahip           | Son Review  |
| ----------------------------- | -------------------- | --------------- | ----------- |
| ./DEVELOPMENT_PLAN_SUMMARY.md | Monthly              | CEO/CTO         | 13 Oct 2025 |
| DEVELOPMENT_ROADMAP.md        | Quarterly            | Product Manager | 13 Oct 2025 |
| TECHNICAL_EVOLUTION.md        | Quarterly            | CTO/Tech Lead   | 13 Oct 2025 |
| ./SPRINT_PLANNING.md          | Per Sprint (2 weeks) | Scrum Master    | 13 Oct 2025 |
| GO_LIVE_PLAYBOOK.md           | On-demand (incident) | DevOps Lead     | 13 Oct 2025 |
| ML_SPRINT3_GUIDE.md           | Monthly              | ML Lead         | 13 Oct 2025 |

---

## 📅 Öneri: Okuma Planı (İlk Hafta)

### Day 1 (Monday)

- [ ] **Herkes:** [./DEVELOPMENT_PLAN_SUMMARY.md](./DEVELOPMENT_PLAN_SUMMARY.md) (5 dk)
- [ ] **CTO/Tech Lead:** [./TECHNICAL_EVOLUTION.md](./TECHNICAL_EVOLUTION.md) (20 dk)
- [ ] **Toplantı:** Kick-off meeting (1 saat) - vizyon alignment

### Day 2 (Tuesday)

- [ ] **Product/Engineering Manager:** [./DEVELOPMENT_ROADMAP.md](./DEVELOPMENT_ROADMAP.md) (30 dk)
- [ ] **Developer:** [./SPRINT_PLANNING.md](./SPRINT_PLANNING.md) (15 dk)
- [ ] **Toplantı:** Sprint 9 planning (2 saat)

### Day 3 (Wednesday)

- [ ] **DevOps:** [./GO_LIVE_PLAYBOOK.md](./GO_LIVE_PLAYBOOK.md) (10 dk)
- [ ] **ML Engineer:** [./ML_SPRINT3_GUIDE.md](./ML_SPRINT3_GUIDE.md) (10 dk)
- [ ] **Aksiyon:** Setup monitoring dashboards

### Day 4 (Thursday)

- [ ] **Developer:** Sprint 9 implementation başlangıç
- [ ] **DevOps:** Infrastructure audit (current state validation)

### Day 5 (Friday)

- [ ] **Retrospective:** İlk haftanın learnings
- [ ] **Toplantı:** Weekly sync (30 dk)

---

## 🎯 Hızlı Referans: Kritik Kararlar

### Karar 1: Microservice Migration (Yes/No)

- **Doküman:** [./TECHNICAL_EVOLUTION.md](./TECHNICAL_EVOLUTION.md), Bölüm: "Migration Roadmap"
- **Timeline:** 6 ay
- **Cost:** $72/mo → $1,440/mo (6th month)
- **Risk:** Orta (strangler fig pattern ile mitigate edilebilir)
- **Öneri:** ✅ YES (scaling için gerekli)

### Karar 2: Kubernetes vs Stay on Docker Compose

- **Doküman:** [./TECHNICAL_EVOLUTION.md](./TECHNICAL_EVOLUTION.md), Bölüm: "Phase 2: Kubernetes Migration"
- **Timeline:** 2 ay (month 4-5)
- **Cost:** +$200/mo (managed K8s)
- **Risk:** Yüksek (learning curve)
- **Öneri:** ✅ YES (enterprise requirement, >100 users)

### Karar 3: Monetization Launch Timeline

- **Doküman:** [./DEVELOPMENT_PLAN_SUMMARY.md](./DEVELOPMENT_PLAN_SUMMARY.md), Bölüm: "Sprint 12: Monetization"
- **Timeline:** 3 ay (month 8-10)
- **Cost:** Stripe fee (2.9% + $0.30)
- **Risk:** Düşük
- **Öneri:** ✅ YES (gelir kritik, erken başla)

### Karar 4: ML RL (Reinforcement Learning) Investment

- **Doküman:** [./DEVELOPMENT_ROADMAP.md](./DEVELOPMENT_ROADMAP.md), Bölüm: "Sprint 10.3: RL Policy"
- **Timeline:** 3 hafta (month 3)
- **Cost:** GPU instance (+$450/mo)
- **Risk:** Yüksek (experimental, Sharpe improvement belirsiz)
- **Öneri:** 🟡 MAYBE (Sprint 10.1-10.2'den sonra re-evaluate)

---

## 📞 İletişim & Feedback

### Doküman sahipliği

- **./DEVELOPMENT_PLAN_SUMMARY.md:** @siyahkare (Onur)
- **DEVELOPMENT_ROADMAP.md:** @siyahkare (Onur)
- **TECHNICAL_EVOLUTION.md:** @siyahkare (Onur)
- **./SPRINT_PLANNING.md:** @siyahkare (Onur)

### Feedback toplama

- **Slack:** #planning-feedback
- **GitHub Issues:** Label: `documentation`
- **Quarterly Review:** Notion page (link TBD)

---

## ✅ Checklist: Dokümanlar Okunduktan Sonra

### CEO/Founder

- [ ] Bütçe onayı (infra cost increase)
- [ ] Hiring approval (1-2 developer)
- [ ] Go-live approval (Sprint 9-10)

### CTO/Tech Lead

- [ ] Service boundary POC (ML Service)
- [ ] K8s cluster trial (AWS EKS free tier)
- [ ] Team upskilling plan (CKA, Go courses)

### Product Manager

- [ ] Sprint 9-10 backlog grooming
- [ ] User story validation
- [ ] Success metrics definition

### Developer

- [ ] Sprint 9 story pickup
- [ ] Development environment setup
- [ ] Code review buddy assignment

### DevOps/SRE

- [ ] Monitoring dashboard setup
- [ ] Alert configuration (PagerDuty, Slack)
- [ ] Backup validation

---

## 🚀 Next Steps (This Week)

1. **All:** Read [./DEVELOPMENT_PLAN_SUMMARY.md](./DEVELOPMENT_PLAN_SUMMARY.md) (5 min)
2. **Leadership:** Approve budget & hiring
3. **Team:** Sprint 9 kick-off meeting (Tuesday)
4. **DevOps:** Run `make prod-ready` (validate current state)
5. **Developer:** Start Story 9.1.1 (ClickHouse optimization)

---

**Doküman Versiyonu:** 1.0  
**Oluşturan:** Onur Mutlu (@siyahkare)  
**Son Güncelleme:** 13 Ekim 2025  
**Sonraki Review:** 1 Kasım 2025

---

> **"Plan the work, work the plan."**  
> — Baron (Onur Mutlu)
