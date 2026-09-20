# AEGIS-Trust: Real-Time High-Throughput Fraud Detection & Verification Pipeline

> **Production-grade Identity & Transaction Risk Engine designed for sub-50ms SLA targets.**  
> Aligned with **IDfy's core product ecosystem**: **OnboardIQ** (Identity Verification), **OneRisk** (Transaction & Velocity Risk), and **Privy** (DPDPA 2023 Compliance & Cryptographic Audit Ledger).

---

## 1. Executive Summary & IDfy Alignment

| IDfy Product | AEGIS-Trust Architectural Feature | Implementation & Technical Design |
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
   [ FastAPI Gateway / Rate Limiter ]  <── Redis Caching / Sliding Window (Sub-50ms Latency)
               │
               ├──► [ Rule Engine (Deterministic) ]  ── (Velocity Checks, Blacklists, PAN/Aadhaar)
               ├──► [ C++ Anomaly / ML Scorer ]     ── (Shannon Entropy & EWMA Variance)
               │
               ▼
   [ Event Worker / Worker Queue ]
               │
               ├──► [ PostgreSQL / SQLite ] ────────── (Auditable Ledger & DPDPA Compliance)
               └──► [ React Dashboard (SSE) ] ──────── (Real-Time Risk & Fraud Metrics)
```

### End-to-End Execution Flow
1. **Gateway Ingestion & Rate Limiting:** FastAPI gateway validates payloads with Pydantic v2. Rate limiter evaluates IP/device velocity via sliding-window counter in $<0.2\text{ms}$.
2. **Parallel Hybrid Evaluation Pipeline:**
   - **Deterministic Rule Engine:** Validates PAN structure, executes Aadhaar Verhoeff checksum algorithm, screens disposable domains (`mailinator.com`, etc.), flags proxy/TOR IP subnets.
   - **C++ SIMD Native Accelerator (`libaegis.so`):** Computes Shannon token entropy (`-sum(p*log2(p))`), character class clusters, and EWMA deviation in $<50\mu\text{s}$ via zero-overhead `ctypes` bindings.
3. **DPDPA Ledger & Cryptographic Lineage:**
   - Column-level symmetric encryption encrypts PII before persisting to the database.
   - Appends transactional decision to an **immutable SHA-256 hash chain** ($Block_n = \text{SHA256}(Seq_n \parallel Timestamp \parallel Payload \parallel Hash_{n-1})$).
4. **Real-Time Broadcasting:** Events are streamed to the React monitoring dashboard via Server-Sent Events (SSE).

---

## 3. SLA & Performance Benchmarks

AEGIS-Trust is engineered for high throughput and sub-50ms latency SLAs:

```
----------------------------------------------------------------------
BENCHMARK RESULTS (200 Sequential End-to-End Verification Pipeline Calls)
----------------------------------------------------------------------
Total Requests Completed:   200 / 200 (100.0% Success)
Total Wall Time:            5.05 seconds
Throughput:                 39.6 req/sec (Single-Process TestClient)
Min Latency:                16.78 ms
P50 Median Latency:         22.98 ms
P90 Latency:                36.60 ms
P95 Latency:                40.80 ms
P99 Latency:                47.08 ms
Max Latency:                48.04 ms
Sub-50ms SLA Compliance:    100.00%
Internal Engine Run Time:   0.05 ms - 0.20 ms
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
backend/aegis/config.py                     40      1    98%
backend/aegis/core/audit.py                 38      1    97%
backend/aegis/models/schemas.py             53      2    96%
backend/aegis/engine/pipeline.py            58      4    93%
backend/aegis/services/storage.py          110     12    89%
backend/aegis/main.py                       54      7    87%
backend/aegis/core/security.py              78     11    86%
backend/aegis/api/v1/verify.py              43      6    86%
backend/aegis/api/v1/reviews.py             27      4    85%
backend/aegis/engine/cpp_bindings.py       133     21    84%
backend/aegis/engine/anomaly_scorer.py      61     12    80%
backend/aegis/engine/rule_engine.py         95     22    77%
backend/aegis/core/rate_limiter.py          88     28    68%
backend/aegis/services/event_stream.py      39     17    56%
------------------------------------------------------------
TOTAL                                     1151    171    85%
======================== 32 passed, 2 warnings in 3.28s ========================
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
│   │   ├── cpp/                # C++20 Shannon Entropy & EWMA Anomaly Engine
│   │   ├── engine/             # C++ ctypes bindings, rule engine, ensemble pipeline
│   │   ├── models/             # SQLAlchemy ORM models & Pydantic v2 schemas
│   │   └── services/           # Storage, Redis sliding window, SSE broadcaster
│   ├── tests/                  # 32 unit and integration tests (PyTest)
│   ├── Dockerfile              # Multi-stage C++ builder + Python runner
│   └── requirements.txt
├── frontend/
│   ├── src/                    # React 19 + Vite dashboard (Anti-vibecode clean UX)
│   ├── Dockerfile              # Multi-stage Node builder + Nginx runner
│   └── nginx.conf
├── benchmarks/
│   └── latency_test.py         # Sub-50ms SLA benchmark tool
├── docker-compose.yml          # Multi-container orchestration (API, Frontend, Postgres, Redis)
├── Makefile                    # Build, test, and run automation
└── README.md
```

---

## 7. Quickstart Guide

### Option A: Local Native Setup (Recommended for testing)

#### 1. Build C++ Engine & Install Python Dependencies
```bash
# Compile C++ shared library
make build-cpp

# Install dependencies in virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

#### 2. Run Tests & Latency Benchmark
```bash
# Run unit & integration test suite with coverage
make test

# Run sub-50ms SLA benchmark
make benchmark
```

#### 3. Build Frontend & Start Server
```bash
# Build React frontend
make build-frontend

# Start AEGIS-Trust server
make run
```
Open **`http://localhost:8000`** in your browser to access the Analyst Dashboard, or **`http://localhost:8000/docs`** for interactive Swagger API documentation.

Default Analyst Credentials:
- **Username:** `analyst_admin`
- **Password:** `AegisSecure@2026`

---

### Option B: Docker Compose (Full Microservices Stack)

```bash
docker-compose up --build
```
- Frontend Dashboard: `http://localhost:3000`
- Backend API Gateway: `http://localhost:8000`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

---

## 8. Interview Talking Points

1. **Sub-50ms SLA Delivery:**
   Explain the dual-engine design: deterministic rules and C++ SIMD Shannon entropy run in parallel in $<0.2\text{ms}$. Sliding window rate limiting uses in-memory deque or Redis Sorted Sets.
2. **DPDPA 2023 & IDfy Privy Integration:**
   Demonstrate column-level encryption, HMAC blind indexing (enabling fast duplicate search without decrypting), and SHA-256 hash chaining for tamper-evident auditability.
3. **Engineering Rigor & TDD:**
   Demonstrate 32 test cases, 85% test coverage, circuit breaker patterns for Redis failover, and strict Pydantic v2 schemas.
