# Veles Shield: Deployment Notes

> **Target Environment:** Enterprise Linux / Cloud Kubernetes (AWS EKS, GCP GKE, Azure AKS)  
> **Scope:** The Compose and Kubernetes files are deployment examples, not a validated production platform. No zero-downtime, latency SLA, or regulatory compliance claim is made by these templates.

Local development defaults to no authentication for the dashboard demo. Never expose that mode to a shared network. Production startup requires `ENVIRONMENT=production`, `AUTH_ENABLED=true`, and strong externally managed secrets. The included dashboard currently targets the local demo workflow; a production deployment must provide an authenticated dashboard/API client.

---

## 1. System Requirements & Prerequisites

### Illustrative starting point only (not capacity-tested)

The following is a rough environment example, not a minimum supported specification or evidence of an SLA. Benchmark with the chosen database, traffic shape, native-engine build, and deployment topology.
- **CPU:** 4 vCPUs as an initial evaluation size; no specific vector instruction set is required by the current default compiler flags.
- **RAM:** 8 GB
- **Storage:** 50 GB NVMe SSD (PostgreSQL WAL + Redis AOF persistence)
- **Network:** 1 Gbps NIC, sub-millisecond local network latency to Redis & Database

### Software Prerequisites
- **Docker Engine:** v24.0+ & Docker Compose v2.20+
- **Kubernetes:** v1.28+ (for cluster deployment)
- **Python:** 3.12+ (or runner container)
- **Redis:** 7.0+ (Standalone, Sentinel, or Cluster)
- **PostgreSQL:** 15+ or 16+

---

## 2. Environment Variables & Secret Configuration

Configure `/app/.env` or mount Kubernetes secrets (`veles-secrets`):

| Variable | Type | Description | Production Recommendation |
| :--- | :--- | :--- | :--- |
| `ENVIRONMENT` | `string` | Deployment environment | Set to `production`. |
| `DEBUG` | `bool` | FastAPI debug mode | **Must be `false`**. |
| `AUTH_ENABLED` | `bool` | API authentication switch | Must be `true` in production; local default is `false`. |
| `SECRET_KEY` | `string` | JWT signature & blind index key | Min 32 random characters: `openssl rand -hex 32`. |
| `AEGIS_ENCRYPTION_KEY` | `string` | 32-byte urlsafe base64 Fernet key | Base64 32-byte key: `Fernet.generate_key()`. |
| `DATABASE_URL` | `string` | SQLAlchemy connection string | `postgresql+psycopg2://user:pass@host:5432/veles_shield` |
| `REDIS_URL` | `string` | Redis connection URI | `redis://redis-cluster:6379/0` |
| `REDIS_ENABLED` | `bool` | Redis rate limiting toggle | Set to `true`. |
| `SLA_MAX_LATENCY_MS`| `float` | Decision-processing target in ms | Default: `50.0`; not an end-to-end guarantee. |

---

## 3. Deployment Option A: Docker Compose Microservices

Recommended for staging, single-server edge instances, and on-premise evaluation.

The included Compose configuration sets production mode and authentication on. It does not create user accounts; the repository has no operator provisioning endpoint. Configure an approved provisioning process before using protected routes.

### Step 1: Pre-flight Initialization
```bash
# Verify environment and compile local artifacts if building on-host
./scripts/init_services.sh
```

### Step 2: Launch Containers
```bash
# Deploy all 4 microservices in detached mode
sudo docker compose up --build -d
```

### Step 3: Verify Status & Health
```bash
# Check container status
sudo docker compose ps

# Test API Gateway Health probe
curl -s http://localhost:8000/health | jq .

# Test Frontend Dashboard HTTP response
curl -I http://localhost:3000
```

### Step 4: Graceful Teardown
```bash
sudo docker compose down
```

---

## 4. Deployment Option B: Kubernetes example manifests

The `k8s/` directory contains starter manifests. Review secret handling, network policies, probes, resource limits, persistent storage, ingress TLS, authentication, migrations, and rollout behavior for the target cluster before use.

### 1. Apply Namespace, ConfigMap & Secrets
```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap-secrets.yaml
```

### 2. Deploy Redis & PostgreSQL Infrastructure
```bash
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/postgres-statefulset.yaml

# Wait for database initialization
kubectl rollout status statefulset/veles-postgres -n veles-shield
kubectl rollout status deployment/veles-redis -n veles-shield
```

### 3. Deploy API Gateway & Frontend Dashboard
```bash
kubectl apply -f k8s/veles-api-deployment.yaml
kubectl apply -f k8s/veles-frontend-deployment.yaml
kubectl apply -f k8s/ingress.yaml

# Confirm rolling update status
kubectl rollout status deployment/veles-api -n veles-shield
kubectl rollout status deployment/veles-frontend -n veles-shield
```

### 4. Verification in Kubernetes
```bash
kubectl get pods -n veles-shield
kubectl logs -l app=veles-api -n veles-shield --tail=50
```

---

## 5. Redis High-Availability Configuration

For deployments that require Redis high availability, evaluate Sentinel or a managed Redis service. Capacity must be measured for the selected workload and topology.

### Production `redis.conf` Directives:
```conf
# Binding and networking
bind 0.0.0.0
port 6379
tcp-backlog 2048
timeout 0
tcp-keepalive 60

# Memory Management & LRU Eviction
maxmemory 2gb
maxmemory-policy volatile-lru

# Persistence Strategy: Low Latency AOF
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite yes
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
```

---

## 6. PostgreSQL Production Tuning & Connection Pooling

When running at enterprise scale, direct database connections from 20+ worker pods can exhaust PostgreSQL connection limits. Deploy **PgBouncer** in transaction pooling mode:

```ini
[databases]
veles_shield = host=127.0.0.1 port=5432 dbname=veles_shield

[pgbouncer]
listen_port = 6432
listen_addr = 0.0.0.0
auth_type = md5
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 30
min_pool_size = 10
reserve_pool_size = 5
```

---

## 7. Cryptographic Key Management & Rotation Runbook

### 7.1 Key Generation
Generate production secrets using cryptographically secure PRNGs:
```bash
# Generate Fernet 256-bit Encryption Key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Generate JWT & Blind Index HMAC Secret
openssl rand -hex 32
```

### 7.2 Zero-Downtime Key Rotation Procedure
1. Deploy the new encryption key as `VELES_ENCRYPTION_KEY_NEW`.
2. Configure `MultiFernet([Fernet(KEY_NEW), Fernet(KEY_OLD)])`.
   - New records are encrypted with `KEY_NEW`.
   - Existing records can still be decrypted with `KEY_OLD`.
3. Execute background re-encryption worker to update historical database records:
   ```python
   # Batch decrypt with old key and re-encrypt with new key
   record.encrypted_full_name = new_cipher.encrypt(old_cipher.decrypt(record.encrypted_full_name))
   ```
4. Once all records are upgraded, retire `KEY_OLD`.

---

## 8. Incident Response & Troubleshooting Runbook

### Issue 1: Processing-time target exceeded
- **Diagnostic:** Check `/api/v1/metrics/latency`.
- **Cause 1: Redis Network Latency:**
  - Verify Redis ping: `make redis-ping`. If ping latency $>5\text{ms}$, inspect network hops or noisy neighbors.
  - The built-in circuit breaker will automatically engage if timeouts exceed 200ms.
- **Cause 2: Database Contention:**
  - Check active PostgreSQL transactions: `SELECT * FROM pg_stat_activity WHERE state != 'idle';`.

### Issue 2: DPDPA Audit Chain Integrity Failure
- **Diagnostic:** `/api/v1/dpdpa/audit-ledger/verify` returns `"tamper_detected": true`.
- **Action:**
  1. Note the `compromised_sequence_number` in the response.
  2. Query that specific block: `SELECT * FROM audit_ledger WHERE sequence_number = X;`.
  3. Compare timestamp against database binary log / WAL to determine which session or actor attempted an unauthorized write.
  4. Escalate immediately to the Data Protection Officer (DPO).
