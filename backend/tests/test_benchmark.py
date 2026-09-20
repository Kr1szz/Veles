import pytest
import time


def test_sub_50ms_sla_benchmark(client):
    """
    Sub-50ms SLA Verification Benchmark.
    Executes a burst of 50 KYC verification requests through the complete pipeline
    (deterministic rules + C++ entropy engine + column encryption + audit logging)
    and verifies that P95 latency is well within 50ms.
    """
    latencies = []
    iterations = 50

    base_payload = {
        "full_name": "Benchmark User",
        "email": "benchmark.user@example.com",
        "phone": "+919876543210",
        "id_type": "PAN",
        "id_number": "ABCPE1234F",
        "country_code": "IN",
        "device_fingerprint": "dev_bench_node",
        "ip_address": "103.21.244.2",
        "consent_given": True,
        "consent_purpose": "Performance Benchmark"
    }

    for i in range(iterations):
        payload = base_payload.copy()
        payload["full_name"] = f"Benchmark User {i}"
        payload["email"] = f"benchmark.user{i}@example.com"

        start = time.perf_counter()
        resp = client.post("/api/v1/verify/kyc", json=payload)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        assert resp.status_code == 200
        latencies.append(elapsed_ms)

    latencies.sort()
    p50 = latencies[int(iterations * 0.50)]
    p95 = latencies[int(iterations * 0.95)]
    p99 = latencies[int(iterations * 0.99)]

    print(f"\n[BENCHMARK] Total: {iterations} runs | P50: {p50:.2f}ms | P95: {p95:.2f}ms | P99: {p99:.2f}ms")

    # Assert sub-50ms SLA
    assert p95 < 50.0, f"P95 latency {p95:.2f}ms violated sub-50ms SLA target!"
