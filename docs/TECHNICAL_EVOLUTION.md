# 🔧 LeviBot Teknik Evrim ve Modernizasyon Planı

**Hedef:** Mevcut monolith'ten microservice-ready, cloud-native sisteme geçiş  
**Zaman Çerçevesi:** 6-12 ay  
**Yaklaşım:** Incremental, zero-downtime migrations

---

## 📊 Mevcut Mimari (v1.6.1)

### Sistem Bileşenleri

```
┌─────────────────────────────────────────┐
│         Telegram Bot + Mini App         │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│    FastAPI Monolith (single process)    │
│  ┌──────────┬──────────┬──────────────┐ │
│  │ Signals  │ ML Model │ Risk Engine  │ │
│  └──────────┴──────────┴──────────────┘ │
└─────────────────┬───────────────────────┘
                  │
        ┌─────────┼─────────┐
        │         │         │
┌───────▼───┐ ┌──▼────┐ ┌──▼──────┐
│ClickHouse │ │ Redis │ │TimescDB │
└───────────┘ └───────┘ └─────────┘
```

### Güçlü Yanlar ✅

- Basit deployment (docker-compose up)
- Düşük latency (process içi çağrılar)
- Kolay debugging (tek process)
- Az operasyonel yük

### Zayıf Yanlar ❌

- Horizontal scaling zor (stateful singleton'lar var)
- Resource contention (CPU-heavy ML vs I/O-heavy API)
- Blast radius büyük (bir bileşen crash → tüm sistem down)
- Teknoloji esnekliği yok (her şey Python FastAPI)

---

## 🎯 Hedef Mimari (v2.0 - Cloud Native)

### Microservice Breakdown

```
┌─────────────────────────────────────────────────┐
│              API Gateway (Nginx/Kong)           │
└────────┬────────────────────────────────────────┘
         │
    ┌────┼────┬─────────┬────────────┬──────────┐
    │    │    │         │            │          │
┌───▼┐ ┌─▼─┐ ┌▼───┐ ┌───▼───┐ ┌─────▼─────┐ ┌──▼──┐
│Auth│ │API│ │ML  │ │Trading│ │Telegram   │ │Data │
│Svc │ │Svc│ │Svc │ │Engine │ │Bot Worker │ │Feed │
└────┘ └───┘ └────┘ └───────┘ └───────────┘ └─────┘
   │     │     │       │          │            │
   └─────┴─────┴───────┴──────────┴────────────┘
                        │
              ┌─────────▼─────────┐
              │   Message Bus     │
              │  (Kafka/RabbitMQ) │
              └───────────────────┘
                        │
         ┌──────────────┼──────────────┐
         │              │              │
    ┌────▼────┐  ┌─────▼─────┐  ┌────▼────┐
    │PostgreSQL│  │   Redis   │  │  S3     │
    │(TimescDB)│  │  Cluster  │  │(MinIO)  │
    └──────────┘  └───────────┘  └─────────┘
```

### Service Boundaries

- **Auth Service:** JWT issue/verify, API key management
- **API Service:** HTTP interface, request routing
- **ML Service:** Model serving, predictions, feature store
- **Trading Engine:** Strategy execution, order management, risk
- **Telegram Bot Worker:** Message handling, webhooks
- **Data Feed:** Market data ingestion, normalization

---

## 🛤️ Migration Roadmap

### Phase 1: Strangler Fig Pattern (3 ay)

**Hedef:** Yeni servisleri eski sisteme paralel ekle, trafiği kademeli kaydır

#### Month 1: Service Extraction Prep

- [ ] **Service boundaries tespit et**
  - [ ] Domain-Driven Design (DDD) analizi
  - [ ] Bounded context'leri belirle (Auth, ML, Trading, Telegram)
  - [ ] Service dependency graph çıkar
  - [ ] API contract'ları tanımla (OpenAPI specs)
- [ ] **Shared data migration stratejisi**
  - [ ] Database per service (ideal) vs shared DB (pragmatic)
  - [ ] Event sourcing candidates (trading events)
  - [ ] CQRS pattern for read-heavy queries
- [ ] **Infrastructure as Code (IaC)**
  - [ ] Terraform for AWS/GCP resources
  - [ ] Kubernetes manifests (Helm charts)
  - [ ] CI/CD pipeline per service (GitHub Actions)

#### Month 2: First Service Extraction (ML Service)

**Neden ML Service ilk?** → En CPU-intensive, en iyi scaling adayı

- [ ] **ML Service API**
  ```python
  # New service: ml-service/
  POST /predict
  POST /retrain
  GET /models
  POST /models/activate
  GET /health
  ```
- [ ] **Dual-write period**
  - [ ] Monolith hala mevcut ML logic'i kullanıyor
  - [ ] ML Service shadow mode'da çalışıyor (log only)
  - [ ] Performance comparison (latency, accuracy)
- [ ] **Traffic cutover**
  - [ ] Week 1: 10% traffic → ML Service (canary)
  - [ ] Week 2: 50% traffic
  - [ ] Week 3: 100% traffic
  - [ ] Week 4: Remove ML code from monolith

#### Month 3: Second Service (Trading Engine)

- [ ] **Trading Engine API**
  ```python
  POST /orders/create
  GET /orders/{id}
  POST /strategies/{name}/start
  POST /strategies/{name}/stop
  GET /portfolio/summary
  ```
- [ ] **Event-driven architecture**
  - [ ] Kafka topic: `signals` (ML Service → Trading Engine)
  - [ ] Kafka topic: `orders` (Trading Engine → downstream)
  - [ ] Event schema registry (Avro/Protobuf)
- [ ] **Traffic cutover** (same 4-week process)

### Phase 2: Kubernetes Migration (2 ay)

#### Month 4: K8s Setup & Stateless Services

- [ ] **K8s cluster setup**
  - [ ] EKS (AWS) / GKE (GCP) / AKS (Azure)
  - [ ] Node pools (ml-pool: GPU, api-pool: CPU)
  - [ ] Ingress (Nginx Ingress Controller)
  - [ ] Service mesh evaluation (Istio vs Linkerd)
- [ ] **Migrate stateless services**
  - [ ] API Service → K8s deployment (3 replicas)
  - [ ] ML Service → K8s deployment (2 replicas, GPU node)
  - [ ] Horizontal Pod Autoscaler (HPA)
  - [ ] Liveness/readiness probes

#### Month 5: Stateful Services & Persistence

- [ ] **Database operators**
  - [ ] PostgreSQL operator (Zalando, Crunchy Data)
  - [ ] Redis operator (Redis Enterprise)
  - [ ] ClickHouse on K8s (Altinity operator)
- [ ] **Persistent Volumes**
  - [ ] StorageClass (EBS, GCE PD, Azure Disk)
  - [ ] StatefulSet for databases
  - [ ] Backup strategy (Velero, K8s snapshots)
- [ ] **Secrets management**
  - [ ] Sealed Secrets / External Secrets Operator
  - [ ] AWS Secrets Manager / GCP Secret Manager
  - [ ] Rotate secrets (90-day policy)

### Phase 3: Observability & Reliability (2 ay)

#### Month 6: Monitoring Stack

- [ ] **Prometheus + Grafana (K8s native)**
  - [ ] Prometheus Operator
  - [ ] Service monitors (auto-discover)
  - [ ] Alertmanager (PagerDuty integration)
  - [ ] Grafana dashboards per service
- [ ] **Distributed tracing**
  - [ ] Jaeger Operator
  - [ ] OpenTelemetry collector
  - [ ] Trace sampling (1% always, 100% errors)
- [ ] **Log aggregation**
  - [ ] Loki (lightweight, like Prometheus for logs)
  - [ ] Fluentd/Fluent Bit (log shipper)
  - [ ] Grafana Explore (unified logs + traces)

#### Month 7: SRE Best Practices

- [ ] **SLOs & Error Budgets**
  - [ ] Define SLIs (latency, availability, error rate)
  - [ ] Set SLOs (99.9% uptime, P95 <100ms)
  - [ ] Error budget tracking (Sloth SLO framework)
- [ ] **Chaos Engineering**
  - [ ] Chaos Mesh or Litmus Chaos
  - [ ] Kill random pods (weekly drill)
  - [ ] Network latency injection
  - [ ] DB failure simulation
- [ ] **Disaster Recovery**
  - [ ] Multi-region setup (active-passive)
  - [ ] Cross-region DB replication
  - [ ] DR drill (quarterly)
  - [ ] RTO: 1 hour, RPO: 5 minutes

### Phase 4: Advanced Features (3-6 ay)

#### Month 8-9: Event-Driven & Async

- [ ] **Message bus (Kafka or RabbitMQ)**
  - [ ] Kafka Operator (Strimzi)
  - [ ] Topics: signals, orders, trades, alerts
  - [ ] Consumer groups (at-least-once vs exactly-once)
  - [ ] Dead letter queues
- [ ] **Event sourcing**
  - [ ] Trading event store (append-only log)
  - [ ] Event replay capability
  - [ ] Time-travel debugging
- [ ] **CQRS (Command Query Responsibility Segregation)**
  - [ ] Write model (PostgreSQL)
  - [ ] Read model (ClickHouse, Redis)
  - [ ] Eventual consistency

#### Month 10-12: ML Platform

- [ ] **Kubeflow or MLflow on K8s**
  - [ ] Model training pipelines (Argo Workflows)
  - [ ] Distributed training (Horovod, Ray)
  - [ ] Model registry (MLflow Model Registry)
  - [ ] A/B testing (KFServing, Seldon Core)
- [ ] **Feature store (Feast)**
  - [ ] Online store (Redis, DynamoDB)
  - [ ] Offline store (S3, BigQuery)
  - [ ] Feature serving (<5ms P99)
- [ ] **GPU optimization**
  - [ ] TensorRT optimization (inference)
  - [ ] Mixed precision (FP16)
  - [ ] Batch inference (reduce GPU idle)
  - [ ] GPU sharing (fractional GPUs)

---

## 🗄️ Database Evolution

### Current State (v1.6.1)

```
TimescaleDB (PostgreSQL)
  - tick_raw (1M rows/day)
  - tick_m1s, tick_m5s (continuous aggregates)

ClickHouse
  - events (JSONL import daily)
  - audit_logs

Redis
  - Rate limiting counters
  - Hot cache (feature vectors)
```

### Target State (v2.0)

```
PostgreSQL (TimescaleDB)
  - Core OLTP (users, api_keys, subscriptions)
  - Write-heavy, ACID required
  - Replicated (primary + 2 replicas)

ClickHouse Cluster
  - Analytics, event logs, audit (append-only)
  - 3 shards, 2 replicas per shard
  - Distributed table (sharded by symbol)

Redis Cluster
  - Session store, cache, rate limit
  - 3 masters, 3 replicas
  - Redis Sentinel for HA

S3 (MinIO in dev)
  - Model artifacts (*.skops, *.onnx)
  - Training datasets (Parquet)
  - Log archives (gzip)
```

### Migration Strategy

1. **Dual-write period** (1 month)
   - Write to both old & new DB
   - Compare results (consistency check)
2. **Read cutover** (1 week)
   - Read from new DB, fallback to old if missing
3. **Old DB decommission** (after 30 days retention)

---

## 🔐 Security Enhancements

### Current (v1.6.1)

- API key auth (plaintext in ENV)
- HMAC cookie auth (admin)
- IP allowlist
- Basic rate limiting

### Target (v2.0)

- [ ] **OAuth2 + OIDC**
  - [ ] Auth Service (Keycloak or Auth0)
  - [ ] JWT with short expiry (5 min)
  - [ ] Refresh token rotation
- [ ] **mTLS (mutual TLS)**
  - [ ] Service-to-service encryption
  - [ ] Certificate rotation (Let's Encrypt)
- [ ] **Secrets management**
  - [ ] Vault, AWS Secrets Manager
  - [ ] Dynamic secrets (DB credentials)
  - [ ] Audit all secret access
- [ ] **Network policies**
  - [ ] K8s NetworkPolicy (deny-by-default)
  - [ ] Service mesh (Istio authorization policies)
- [ ] **Runtime security**
  - [ ] Falco (detect suspicious syscalls)
  - [ ] Trivy (container scanning)
  - [ ] OPA (Open Policy Agent) for admission control

---

## 🌍 Multi-Region Strategy

### Phase 1: Single Region (Active)

- Primary: us-east-1 (AWS) or us-central1 (GCP)
- All services in one VPC
- Availability Zone redundancy (3 AZs)

### Phase 2: Multi-Region (Passive DR)

- Primary: us-east-1
- Failover: eu-west-1
- DB replication (async, 10s lag acceptable)
- DNS failover (Route53, Cloud DNS)
- RTO: 1 hour, RPO: 5 minutes

### Phase 3: Multi-Region (Active-Active)

- US: us-east-1 (50% traffic)
- EU: eu-west-1 (50% traffic)
- Read local, write global (eventual consistency)
- CRDT or conflict resolution strategy
- Latency-based routing

---

## 📈 Scaling Targets

### API Service

- **v1.6.1:** 10 RPS, 1 instance
- **v2.0 (3 mo):** 100 RPS, 3 instances
- **v2.0 (6 mo):** 1,000 RPS, 10 instances (HPA)
- **v2.0 (12 mo):** 10,000 RPS, 50 instances (multi-region)

### ML Service

- **v1.6.1:** 1 prediction/s, CPU only
- **v2.0 (3 mo):** 10 predictions/s, GPU (T4)
- **v2.0 (6 mo):** 100 predictions/s, GPU cluster (2x A10)
- **v2.0 (12 mo):** 1,000 predictions/s, TPU or Inferentia

### Database

- **v1.6.1:** 1M rows/day (single instance)
- **v2.0 (3 mo):** 10M rows/day (primary + 1 replica)
- **v2.0 (6 mo):** 100M rows/day (sharded, 3 shards)
- **v2.0 (12 mo):** 1B rows/day (distributed, 10 shards)

---

## 💰 Infrastructure Cost Estimation

### v1.6.1 (Current)

```
Docker Compose on single VM
- EC2 t3.large ($60/mo)
- EBS 100GB ($10/mo)
- S3 100GB ($2/mo)
---
Total: ~$72/mo
```

### v2.0 (3 months, K8s small)

```
EKS cluster (3 nodes)
- 3x t3.large ($180/mo)
- ALB ($20/mo)
- EBS 300GB ($30/mo)
- RDS PostgreSQL db.t3.medium ($50/mo)
- Redis ElastiCache t3.small ($15/mo)
- S3 500GB ($10/mo)
---
Total: ~$305/mo
```

### v2.0 (6 months, K8s medium)

```
EKS cluster (5 nodes, 1 GPU)
- 4x t3.xlarge ($480/mo)
- 1x g4dn.xlarge GPU ($450/mo)
- ALB ($20/mo)
- EBS 1TB ($100/mo)
- RDS db.r5.large ($200/mo)
- Redis r5.large ($100/mo)
- S3 2TB ($40/mo)
- Data transfer ($50/mo)
---
Total: ~$1,440/mo
```

### v2.0 (12 months, Multi-region)

```
EKS clusters (2 regions, 10 nodes each)
- 20x t3.xlarge ($2,400/mo)
- 4x g4dn.xlarge GPU ($1,800/mo)
- ALB x2 ($40/mo)
- EBS 5TB ($500/mo)
- RDS Multi-AZ db.r5.2xlarge x2 ($1,600/mo)
- Redis Cluster x2 ($800/mo)
- S3 10TB ($200/mo)
- Data transfer ($500/mo)
- CloudFront CDN ($100/mo)
---
Total: ~$7,940/mo
```

**ROI:** At $25K MRR (month 12), infra is 32% of revenue (healthy for SaaS)

---

## 🧪 Testing Strategy

### Pre-Migration Testing

- [ ] **Chaos testing** (kill services, inject latency)
- [ ] **Load testing** (K6, Locust - 10x expected traffic)
- [ ] **Data migration dry-run** (restore from backup, migrate, validate)
- [ ] **Rollback drill** (revert to old system in <15 min)

### During Migration

- [ ] **Canary releases** (10% → 50% → 100%)
- [ ] **Feature flags** (toggle new service on/off)
- [ ] **Smoke tests** (automated, every deploy)
- [ ] **Synthetic monitoring** (Pingdom, Datadog Synthetics)

### Post-Migration

- [ ] **Burn-in period** (2 weeks, no new features)
- [ ] **Performance regression tests** (compare old vs new)
- [ ] **Cost analysis** (actual vs estimated)
- [ ] **Post-mortem** (what went well, what didn't)

---

## 🚨 Rollback Plan

### Triggers

- Error rate >1% for 5 minutes
- Latency P95 >500ms for 10 minutes
- Data inconsistency detected
- Manual decision (incident commander)

### Steps

1. **Stop traffic to new service** (5 min)
   - Update Nginx/Kong routing rules
   - Redirect to old monolith
2. **Verify old system healthy** (5 min)
   - Check health endpoints
   - Validate sample requests
3. **Notify stakeholders** (immediate)
   - Slack #incidents channel
   - Status page update
4. **Root cause analysis** (next day)
   - Logs, traces, metrics review
   - Blameless post-mortem
5. **Fix & retry** (1-2 weeks later)

---

## 📚 Technology Stack Evolution

### Current (v1.6.1)

- **Backend:** Python 3.11, FastAPI, Uvicorn
- **ML:** LightGBM, scikit-learn, PyTorch
- **Databases:** TimescaleDB, ClickHouse, Redis
- **Infra:** Docker Compose, Nginx
- **Monitoring:** Prometheus, Grafana

### Target (v2.0)

- **Backend:** Python 3.12+, FastAPI (still), Go (for high-perf services)
- **ML:** LightGBM, XGBoost, PyTorch, TensorFlow (Keras), ONNX Runtime
- **Databases:** PostgreSQL (TimescaleDB), ClickHouse Cluster, Redis Cluster
- **Message Bus:** Kafka (Strimzi) or RabbitMQ
- **Infra:** Kubernetes (EKS/GKE), Terraform, Helm, Argo CD
- **Monitoring:** Prometheus, Grafana, Loki, Jaeger, OpenTelemetry
- **Service Mesh:** Istio or Linkerd (evaluating)

### Long-term (v3.0 - 18+ months)

- **Edge Computing:** Cloudflare Workers, Lambda@Edge (低延迟预测)
- **Serverless:** AWS Lambda, Cloud Functions (for burst workloads)
- **Blockchain:** Ethereum L2 (token gating, on-chain audit log)
- **Quantum-resistant crypto:** (future-proofing)

---

## 🎓 Team Upskilling Plan

### Required Skills

- [ ] **Kubernetes** (CKA certification recommended)
- [ ] **Go programming** (for performance-critical services)
- [ ] **Distributed systems** (consistency, CAP theorem)
- [ ] **Event-driven architecture** (Kafka, event sourcing)
- [ ] **SRE practices** (SLOs, error budgets, incident response)

### Training Resources

- **Kubernetes:** CNCF courses, Kubernetes the Hard Way
- **Go:** Go by Example, Effective Go
- **Distributed Systems:** Designing Data-Intensive Applications (Martin Kleppmann)
- **SRE:** Google SRE Book (free online)
- **Kafka:** Kafka Definitive Guide

---

## 🏁 Success Criteria

### Migration Successful If:

- ✅ Zero downtime (blue-green or canary)
- ✅ Performance maintained or improved (latency, throughput)
- ✅ Data consistency validated (checksums, row counts)
- ✅ Cost within budget (+20% acceptable)
- ✅ Team confident in new system (runbooks, training complete)

### Rollback If:

- ❌ Data loss detected
- ❌ Performance degradation >20%
- ❌ Unforeseen cost overrun (>50%)
- ❌ Critical bug in production (P0)

---

## 📅 Detailed Timeline (Gantt Chart)

```
Q4 2025
├─ Oct: Phase 1.1 - Service boundaries & IaC
├─ Nov: Phase 1.2 - ML Service extraction
└─ Dec: Phase 1.3 - Trading Engine extraction

Q1 2026
├─ Jan: Phase 2.1 - K8s setup & stateless migration
├─ Feb: Phase 2.2 - Stateful services & persistence
└─ Mar: Phase 3.1 - Monitoring & tracing

Q2 2026
├─ Apr: Phase 3.2 - SRE practices & chaos engineering
├─ May: Phase 4.1 - Kafka & event-driven
└─ Jun: Phase 4.2 - ML platform (Kubeflow, Feast)
```

---

**Doküman Versiyonu:** 1.0  
**Son Güncelleme:** 13 Ekim 2025  
**Sahip:** Onur Mutlu (@siyahkare)  
**Review Cycle:** Quarterly

---

_Bu migration plan, canlı bir dokümandır ve progress'e göre güncellenecektir._
