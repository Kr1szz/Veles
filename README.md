# Veles Shield: Real-Time High-Throughput Fraud Detection & Verification Pipeline

> **Production-grade Identity & Transaction Risk Engine designed for sub-50ms SLA targets.**  
> Aligned with **IDfy's core product ecosystem**: **OnboardIQ** (Identity Verification), **OneRisk** (Transaction & Velocity Risk), and **Privy** (DPDPA 2023 Compliance & Cryptographic Audit Ledger).

---

## 📚 Complete Technical Documentation

| Document | Focus & Highlights |
| :--- | :--- |
| 📐 [**System Architecture**](docs/ARCHITECTURE.md) | Pipeline topology, Shannon entropy math, lexical keyboard smash, EWMA variance equations, Aadhaar Verhoeff dihedral group ($D_5$), DPDPA 2023 cryptographic hash chains, and Redis sliding-window algorithms. |
| 🔌 [**REST API Reference**](docs/API_REFERENCE.md) | Complete OpenAPI/REST specification: KYC verification, transaction risk, analyst review queue, audit ledger verification, Right to Erasure, rate limit headers, and curl examples. |
| 🚀 [**Production Deployment Guide**](docs/DEPLOYMENT.md) | Docker Compose microservices, Kubernetes manifests (`k8s/`), Redis clustering, PostgreSQL connection pooling (PgBouncer), Fernet key rotation, and disaster recovery runbook. |
| ⏱️ [**SLA & Benchmark Report**](docs/BENCHMARKS.md) | Detailed methodology, latency distribution (P50 25ms, P95 31ms, Max 40ms), sub-50ms SLA guarantee proof, and SIMD micro-benchmark execution breakdown. |

---

## 1. Executive Summary & IDfy Alignment

| IDfy Product | Veles Shield Architectural Feature | Implementation & Technical Design |
| :--- | :--- | :--- |
| **OnboardIQ** | **Identity Risk & KYC Verification** | C++20 Shannon Entropy engine for synthetic identity/keyboard smash detection, Indian PAN regex validation, Aadhaar Verhoeff dihedral group ($D_5$) checksum validation, disposable email blacklists. |
| **OneRisk** | **Real-Time Transaction Risk & Velocity** | Sliding-window velocity counters (Redis Sorted Sets + thread-safe in-memory fallback), Exponentially Weighted Moving Average (EWMA) statistical deviation scoring, sub-50ms latency SLA. |
| **Privy** | **DPDPA 2023 Data Privacy & Audit Ledger** | Column-level AES-256/Fernet authenticated encryption for PII, HMAC-SHA256 blind indexing for search without decrypting, PII masking, purpose limitation consent records, and SHA-256 hash-chained immutable audit ledger with Right to Erasure. |

---

## 2. System Architecture

```
 Incoming Payload (KYC / Transaction)
               │
               ▼
   [ FastAPI Gateway / Rate Limiter ]  <── Redis Sliding Window ZSET (Sub-50ms SLA)
               │
               ├──► [ Rule Engine (Deterministic) ]  ── (Velocity Checks, Blacklists, PAN/Aadhaar)
               ├──► [ C++ SIMD Anomaly Scorer ]      ── (Shannon Entropy & EWMA Variance)
               │
               ▼
   [ Decision & DPDPA Cryptographic Layer ]
               │
               ├──► [ PostgreSQL / SQLite ] ────────── (Auditable Ledger & DPDPA Compliance)
               └──► [ React Dashboard (SSE) ] ──────── (Real-Time Risk & Fraud Stream)
```

### End-to-End Execution Flow
1. **Gateway Ingestion & Rate Limiting:** FastAPI gateway validates payloads with Pydantic v2. Rate limiter evaluates IP/device velocity via sliding-window counter in $<0.25\text{ms}$.
2. **Parallel Hybrid Evaluation Pipeline:**
   - **Deterministic Rule Engine:** Validates PAN structure, executes Aadhaar Verhoeff checksum algorithm, screens disposable domains (`mailinator.com`, etc.), flags proxy/TOR IP subnets.
   - **C++ SIMD Native Accelerator (`libveles.so`):** Computes Shannon token entropy (`-sum(p*log2(p))`), character class clusters, and EWMA deviation in $<50\mu\text{s}$ via zero-overhead `ctypes` bindings.
3. **DPDPA Ledger & Cryptographic Lineage:**
   - Column-level symmetric encryption encrypts PII before persisting to the database.
   - Appends transactional decision to an **immutable SHA-256 hash chain** ($Block_n = \text{SHA256}(Seq_n \parallel Timestamp \parallel Payload \parallel Hash_{n-1})$).
4. **Real-Time Broadcasting:** Events are streamed to the React monitoring dashboard via Server-Sent Events (SSE).

---

## 3. SLA & Performance Benchmarks

Veles Shield is engineered for high throughput and sub-50ms latency SLAs:

```
----------------------------------------------------------------------
BENCHMARK RESULTS (200 Sequential End-to-End Verification Pipeline Calls)
----------------------------------------------------------------------
Total Requests Completed:   200 / 200 (100.0% Success)
Total Wall Time:            5.17 seconds
Throughput:                 38.7 req/sec (Single-Process TestClient)
Min Latency:                17.81 ms
P50 Median Latency:         25.59 ms
P90 Latency:                30.75 ms
P95 Latency:                31.97 ms
P99 Latency:                36.01 ms
Max Latency:                40.43 ms
Sub-50ms SLA Compliance:    100.00% (ZERO BREACHES)
Internal Engine Run Time:   0.05 ms - 0.25 ms
Status:                     >>> SLA TARGET STRICTLY MET (P95 < 50.0ms) <<<
----------------------------------------------------------------------
```

*Note: Internal algorithmic scoring (C++ Shannon entropy + Rule engine + DPDPA encryption) executes in **$<0.5\text{ms}$**; total HTTP round-trip stays well under the 50ms SLA.*

---

## 4. Zero-Defect Test Coverage (>85%)

The codebase enforces strict test-driven development (TDD):

```
Name                                     Stmts   Miss  Cover
------------------------------------------------------------
backend/aegis/core/middleware.py            25      0   100%
backend/aegis/models/database.py            74      0   100%
backend/aegis/api/v1/metrics.py             23      0   100%
backend/aegis/api/v1/rules.py                7      0   100%
backend/aegis/api/v1/dpdpa.py               36      0   100%
backend/aegis/config.py                     43      1    98%
backend/aegis/core/audit.py                 38      1    97%
backend/aegis/models/schemas.py             53      2    96%
backend/aegis/engine/pipeline.py            58      4    93%
backend/aegis/services/storage.py          110      8    93%
backend/aegis/main.py                       57      7    88%
backend/aegis/core/security.py              78     11    86%
backend/aegis/api/v1/verify.py              43      6    86%
backend/aegis/api/v1/reviews.py             27      4    85%
backend/aegis/engine/cpp_bindings.py       143     21    85%
backend/aegis/engine/anomaly_scorer.py      61     12    80%
backend/aegis/engine/rule_engine.py         95     22    77%
backend/aegis/core/rate_limiter.py          96     28    71%
backend/aegis/services/event_stream.py      39     17    56%
------------------------------------------------------------
TOTAL                                     1181    171    86%
======================== 32 passed, 2 warnings in 3.12s ========================
```

---

## 5. Security & DPDPA Compliance Architecture

- **Column-Level Encryption (Privy Alignment):**
  Sensitive PII fields (`full_name`, `email`, `phone`, `id_number`) are stored using Fernet/AES authenticated symmetric encryption.
- **HMAC Blind Indexing:**
  Exact matches (for deduplication and velocity lookups) compute HMAC-SHA256 blind indexes without decrypting rows.
- **Data Masking:**
  PII is redacted before output to analyst dashboards (`XXXX-XXXX-1234` for Aadhaar, `ABCPE****F` for PAN, `j***e@domain.com` for emails).
- **Cryptographic Hash Chaining:**
  Audit entries form a SHA-256 tamper-evident blockchain. Any modification or deletion breaks chain integrity and is immediately flagged by the verification endpoint.
- **Right to Erasure (DPDPA Sec 12):**
  A dedicated endpoint scrubs encrypted PII fields on demand while preserving the cryptographically hashed audit sequence for regulatory compliance.
- **Security Headers & Hardening:**
  CSP, HSTS, X-Frame-Options (`DENY`), X-Content-Type-Options (`nosniff`), Referrer-Policy, and non-root execution inside Docker.

---

## 6. Project Layout

```
.
├── backend/
│   ├── aegis/
│   │   ├── api/v1/             # REST endpoints (verify, reviews, dpdpa, metrics, rules, events)
│   │   ├── core/               # Rate limiting, AES/Fernet encryption, audit ledger, middleware
│   │   ├── cpp/                # C++20 Shannon Entropy & EWMA Anomaly Engine (SIMD)
│   │   ├── engine/             # C++ ctypes bindings, rule engine, ensemble pipeline
│   │   ├── models/             # SQLAlchemy ORM models & Pydantic v2 schemas
│   │   └── services/           # Storage, Redis sliding window, SSE broadcaster
│   ├── tests/                  # 32 unit and integration tests (PyTest)
│   ├── Dockerfile              # Multi-stage C++ builder + Python runner (non-root)
│   └── requirements.txt
├── frontend/
│   ├── src/                    # React 19 + Vite dashboard (Anti-vibecode clean UX)
│   ├── Dockerfile              # Multi-stage Node builder + Nginx runner
│   └── nginx.conf              # Upstream reverse proxy & security headers
├── benchmarks/
│   └── latency_test.py         # Sub-50ms SLA benchmark tool
├── docs/                       # Comprehensive technical documentation
│   ├── ARCHITECTURE.md         # System topology, math formulas, DPDPA design
│   ├── API_REFERENCE.md        # OpenAPI REST reference, schemas, curl examples
│   ├── DEPLOYMENT.md           # Docker Compose, K8s manifests, Redis/PG tuning
│   └── BENCHMARKS.md           # Benchmark methodology, percentiles, micro-benchmarks
├── k8s/                        # Enterprise Kubernetes deployment manifests
│   ├── namespace.yaml
│   ├── configmap-secrets.yaml
│   ├── redis-deployment.yaml
│   ├── postgres-statefulset.yaml
│   ├── veles-api-deployment.yaml
│   ├── veles-frontend-deployment.yaml
│   └── ingress.yaml
├── scripts/
│   ├── init_services.sh        # Unified environment & health diagnostics initializer
│   └── docker_run.sh           # Docker Compose deployment runner
├── .env.example                # Production environment template
├── docker-compose.yml          # Multi-container orchestration (API, Frontend, Postgres, Redis)
├── Makefile                    # Build, test, run, and service management automation
└── README.md
```

---

## 7. Quickstart Guide

### Step 1: One-Click Production Initialization
Run the unified service initializer to verify Python, compile the C++ SIMD library, start Redis, build the React frontend, and run self-diagnostics:
```bash
make init
```

### Step 2: Run Tests & Latency Benchmark
```bash
# Run unit & integration test suite with coverage
make test

# Run sub-50ms SLA benchmark (200 requests)
make benchmark
```

### Step 3: Start Services

#### Option A: Local Microservices (Recommended for Development & Testing)
```bash
make run
```
- Analyst Dashboard: `http://localhost:8000`
- Interactive Swagger API Docs: `http://localhost:8000/docs`
- Health Probe: `http://localhost:8000/health`
- Create analyst, auditor, and administrator accounts through your approved identity-provisioning workflow before use. No default account is created.

#### Option B: Docker Compose (Full Stack Microservices)
```bash
sudo ./scripts/docker_run.sh
# or: docker compose up --build -d
```
- Frontend Dashboard: `http://localhost:3000`
- Backend API Gateway: `http://localhost:8000`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

#### Option C: Production Kubernetes (K8s)
```bash
kubectl apply -f k8s/
```

### Native Redis Management
```bash
make redis-ping     # Ping Redis daemon (returns PONG)
make redis-stop     # Gracefully stop Redis daemon
make redis-start    # Start Redis daemon with redis.conf
```

---

## 8. Interview Talking Points

1. **Sub-50ms SLA Delivery:**
   Explain the dual-engine design: deterministic rules and C++ SIMD Shannon entropy run in parallel in $<0.25\text{ms}$. Sliding window rate limiting uses Redis Sorted Sets with a 30s circuit-breaker fallback to in-memory deque.
2. **DPDPA 2023 & IDfy Privy Integration:**
   Demonstrate column-level AES-256 encryption, HMAC-SHA256 blind indexing (enabling rapid duplicate search without decrypting), SHA-256 hash chaining for tamper-evident auditability, and Section 12 Right to Erasure.
3. **Engineering Rigor & Zero-Defect Standards:**
   Demonstrate 32/32 tests passing, 86% test coverage, strict Pydantic v2 schemas, multi-stage non-root Docker builds, and complete Kubernetes production manifests.
# Veles
