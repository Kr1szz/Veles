# Veles Shield: REST API Reference & Specification

> **Base URL:** `http://localhost:8000` (Local) / `http://veles.idfy.internal` (Production)  
> **API Version:** `v1` (`/api/v1`)  
> **Interactive Documentation:** `http://localhost:8000/docs` (Swagger UI) / `http://localhost:8000/redoc` (ReDoc)

---

## 1. Global Headers & Security Conventions

### Request Headers
- `Content-Type: application/json` (Required for POST/PUT payloads)
- `Authorization: Bearer <JWT_ACCESS_TOKEN>` (Required for Analyst & DPDPA administrative endpoints)
- `X-Request-ID: <UUID>` (Optional, auto-generated if omitted for distributed tracing)

### Response Headers
- `X-Response-Time-Ms: <float>`: Exact backend processing duration in milliseconds (measured before serialization).
- `X-Frame-Options: DENY`: Clickjacking protection.
- `X-Content-Type-Options: nosniff`: MIME-type sniffing defense.
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`: Production HSTS header.

---

## 2. Authentication Endpoints (`/api/v1/auth`)

### 2.1 Login & Obtain JWT Bearer Token
**`POST /api/v1/auth/login`**

Authenticates an analyst or administrator and returns an encrypted JWT bearer token.

**Request Payload:**
```json
{
  "username": "analyst_admin",
  "password": "your-provisioned-password"
}
```

**Response (`200 OK`):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 28800,
  "username": "analyst_admin",
  "role": "risk_analyst"
}
```

**Curl Example:**
```bash
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"your-provisioned-user","password":"your-provisioned-password"}'
```

---

### 2.2 Current User Profile
**`GET /api/v1/auth/me`**  
*Requires Authorization header.*

**Response (`200 OK`):**
```json
{
  "username": "analyst_admin",
  "role": "risk_analyst",
  "email": "analyst@veles-shield.idfy",
  "is_active": true
}
```

---

## 3. Verification & Fraud Prevention (`/api/v1/verify`)

### 3.1 KYC & Identity Verification (OnboardIQ Alignment)
**`POST /api/v1/verify/kyc`**

Executes real-time identity fraud assessment using PAN syntax checks, Aadhaar Verhoeff dihedral group validation, disposable email filters, and C++ SIMD Shannon token entropy analysis.

**Request Payload:**
```json
{
  "full_name": "Aarav Sharma",
  "email": "aarav.sharma@gmail.com",
  "phone": "+919876543210",
  "id_type": "PAN",
  "id_number": "ABCPS1234F",
  "ip_address": "103.21.144.2",
  "device_fingerprint": "dfp_browser_chrome_122_x86"
}
```

**Response (`200 OK`):**
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "timestamp": "2026-09-20T06:30:15.123456Z",
  "decision": "APPROVE",
  "risk_score": 0.05,
  "execution_time_ms": 0.18,
  "rules_triggered": [],
  "shannon_entropy": 3.12,
  "masked_identity": {
    "full_name": "Aarav Sharma",
    "email": "a***a@gmail.com",
    "phone": "+9198****3210",
    "id_number": "ABCPS****F"
  }
}
```

**High-Risk Anomaly Example:**
```json
// Request with synthetic keyboard-smash identity and disposable email:
{
  "full_name": "qwxzjlmnptvy",
  "email": "fraudster99@mailinator.com",
  "phone": "+911234567890",
  "id_type": "PAN",
  "id_number": "INVALID_PAN_0000",
  "ip_address": "185.220.101.5"
}

// Response (REJECT):
{
  "id": "e21b8692-0b81-4b11-b0db-6e6e22f28123",
  "timestamp": "2026-09-20T06:31:02.891234Z",
  "decision": "REJECT",
  "risk_score": 0.95,
  "execution_time_ms": 0.22,
  "rules_triggered": [
    "INVALID_PAN_FORMAT",
    "DISPOSABLE_EMAIL_DOMAIN",
    "HIGH_LEXICAL_NAME_ANOMALY",
    "TOR_EXIT_NODE_IP"
  ]
}
```

**Curl Example:**
```bash
curl -s -X POST http://localhost:8000/api/v1/verify/kyc \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Aarav Sharma",
    "email": "aarav.sharma@gmail.com",
    "phone": "+919876543210",
    "id_type": "PAN",
    "id_number": "ABCPS1234F",
    "ip_address": "103.21.144.2"
  }'
```

---

### 3.2 Transaction Risk Assessment (OneRisk Alignment)
**`POST /api/v1/verify/transaction`**

Assesses transactional fraud probability using sliding-window velocity tracking and EWMA statistical deviation scoring.

**Request Payload:**
```json
{
  "user_id": "usr_992812",
  "amount": 250000.0,
  "currency": "INR",
  "payment_method": "UPI",
  "ip_address": "49.36.12.18",
  "device_fingerprint": "dfp_android_14_pixel8",
  "historical_mean": 1200.0,
  "historical_stddev": 400.0
}
```

**Response (`200 OK`):**
```json
{
  "id": "b38101a4-c361-4fa3-80b1-314112e1a2f1",
  "timestamp": "2026-09-20T06:32:00.123456Z",
  "decision": "REVIEW",
  "risk_score": 0.65,
  "execution_time_ms": 0.14,
  "rules_triggered": [
    "EWMA_TRANSACTION_OUTLIER_Z_SCORE_EXCEEDED"
  ],
  "velocity_window_count": 1
}
```

---

### 3.3 Historical Verification Records
**`GET /api/v1/verify/records?limit=20&offset=0&decision=REVIEW`**

Retrieves paginated verification audit logs with masked PII.

---

## 4. Human-In-The-Loop Reviews (`/api/v1/reviews`)

### 4.1 Fetch Analyst Review Queue
**`GET /api/v1/reviews/queue`**

Retrieves items whose risk scores fell between `0.30` and `0.70`, requiring human analyst intervention.

**Response (`200 OK`):**
```json
{
  "total_pending": 1,
  "items": [
    {
      "id": "b38101a4-c361-4fa3-80b1-314112e1a2f1",
      "risk_score": 0.65,
      "decision": "REVIEW",
      "created_at": "2026-09-20T06:32:00.123456Z",
      "rules_triggered": ["EWMA_TRANSACTION_OUTLIER_Z_SCORE_EXCEEDED"],
      "masked_identifier": "usr_992812"
    }
  ]
}
```

---

### 4.2 Analyst Decision Override
**`POST /api/v1/reviews/{id}/override`**  
*Requires Bearer Token.*

Allows an authorized risk analyst to manually approve or reject a flagged transaction, logging an immutable audit record.

**Request Payload:**
```json
{
  "new_decision": "APPROVE",
  "override_reason": "Verified user identity via secondary out-of-band video KYC."
}
```

**Response (`200 OK`):**
```json
{
  "status": "success",
  "record_id": "b38101a4-c361-4fa3-80b1-314112e1a2f1",
  "updated_decision": "APPROVE",
  "analyst": "analyst_admin",
  "audit_hash": "a54f8e6c7104b3..."
}
```

---

## 5. DPDPA 2023 Compliance & Audit Ledger (`/api/v1/dpdpa`)

### 5.1 Immutable Audit Ledger Listing
**`GET /api/v1/dpdpa/audit-ledger?limit=50`**

Retrieves cryptographically hash-chained audit blocks.

**Response (`200 OK`):**
```json
{
  "total_records": 4,
  "records": [
    {
      "sequence_number": 1,
      "timestamp": "2026-09-20T06:30:15.123456Z",
      "action": "KYC_VERIFICATION",
      "entity_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "current_hash": "8f3a9e1d2c...",
      "previous_hash": "0000000000000000000000000000000000000000000000000000000000000000"
    }
  ]
}
```

---

### 5.2 Live Cryptographic Chain Integrity Verification
**`GET /api/v1/dpdpa/audit-ledger/verify`**

Verifies the mathematical integrity of the SHA-256 blockchain from genesis block to tip.

**Response (`200 OK` - Valid State):**
```json
{
  "status": "VALID",
  "total_blocks_verified": 4,
  "integrity_intact": true,
  "genesis_hash": "0000000000000000000000000000000000000000000000000000000000000000",
  "latest_hash": "9c12b7a8...",
  "tamper_detected": false
}
```

---

### 5.3 Right to Erasure (DPDPA Section 12)
**`POST /api/v1/dpdpa/erasure`**  
*Requires Bearer Token.*

Securely obliterates encrypted PII fields and severs blind indexes while recording a compliance audit block.

**Request Payload:**
```json
{
  "identifier": "aarav.sharma@gmail.com",
  "reason": "Customer Consent Revocation pursuant to DPDPA 2023 Section 12"
}
```

**Response (`200 OK`):**
```json
{
  "status": "success",
  "message": "PII for requested identifier has been obliterated. Audit lineage preserved.",
  "records_erased": 1,
  "audit_sequence_number": 5
}
```

---

## 6. Real-Time Telemetry & Health

### 6.1 SLA & Latency Metrics
**`GET /api/v1/metrics/latency`**

Returns real-time execution statistics measured across all pipeline invocations.

**Response (`200 OK`):**
```json
{
  "total_requests": 200,
  "min_latency_ms": 17.81,
  "p50_latency_ms": 25.59,
  "p90_latency_ms": 30.75,
  "p95_latency_ms": 31.97,
  "p99_latency_ms": 36.01,
  "max_latency_ms": 40.43,
  "sub_50ms_sla_percent": 100.0,
  "sla_breaches": 0
}
```

---

### 6.2 Health & Readiness Probe
**`GET /health`**

Monitors internal subsystem liveness for Kubernetes and Docker orchestrators.

**Response (`200 OK`):**
```json
{
  "status": "HEALTHY",
  "service": "Veles Shield",
  "version": "1.0.0",
  "cpp_engine_active": true,
  "redis_active": true,
  "sla_target": "<50ms"
}
```
