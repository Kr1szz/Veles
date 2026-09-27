#!/usr/bin/env python3
"""In-process measurement of verification request latency and throughput."""

import sys
import os
import time
import math
import statistics
from typing import List

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from fastapi.testclient import TestClient
from aegis.main import app
from aegis.engine.cpp_bindings import HAS_CPP_ENGINE
from aegis.config import settings


def run_benchmark(num_requests: int = 500):
    print("=" * 70)
    print("Veles Shield: In-process verification latency measurement")
    print(f"Native C++ scorer active: {HAS_CPP_ENGINE}")
    print(f"Target Requests: {num_requests}")
    print("=" * 70)

    client = TestClient(app)
    latencies_ms: List[float] = []
    failed_requests = 0

    # Warmup
    for _ in range(10):
        client.post("/api/v1/verify/kyc", json={
            "full_name": "Warmup Run",
            "email": "warmup@example.com",
            "id_type": "PAN",
            "id_number": "TESTP0000T",
            "consent_given": True
        })

    print(f"Starting test execution of {num_requests} end-to-end verification calls...")
    start_total = time.perf_counter()

    for i in range(num_requests):
        # Varying payload
        payload = {
            "full_name": f"Citizen Applicant {i}",
            "email": f"applicant_{i}@example.com",
            "phone": "+910000000001",
            "id_type": "PAN",
            "id_number": "TESTP0000T",
            "country_code": "IN",
            "device_fingerprint": f"dev_node_{i % 20}",
            "ip_address": f"192.0.2.{i % 250 + 1}",
            "consent_given": True,
            "consent_purpose": "Synthetic local benchmark"
        }

        t0 = time.perf_counter()
        resp = client.post(
            "/api/v1/verify/kyc",
            json=payload,
            headers={"X-Forwarded-For": payload["ip_address"]},
        )
        t_elapsed = (time.perf_counter() - t0) * 1000.0

        if resp.status_code == 200:
            latencies_ms.append(t_elapsed)
        else:
            failed_requests += 1

    total_time = time.perf_counter() - start_total
    rps = len(latencies_ms) / total_time if total_time else 0.0

    if not latencies_ms:
        print(f"No successful requests ({failed_requests} failed). Check API configuration and authentication.")
        return

    latencies_ms.sort()
    count = len(latencies_ms)

    p50 = statistics.median(latencies_ms)
    p90 = latencies_ms[max(0, math.ceil(count * 0.90) - 1)]
    p95 = latencies_ms[max(0, math.ceil(count * 0.95) - 1)]
    p99 = latencies_ms[max(0, math.ceil(count * 0.99) - 1)]
    min_lat = min(latencies_ms)
    max_lat = max(latencies_ms)
    threshold_ms = settings.SLA_MAX_LATENCY_MS
    under_target_count = sum(1 for latency in latencies_ms if latency <= threshold_ms)
    under_target_percentage = (under_target_count / count) * 100.0

    print("\n" + "-" * 70)
    print("BENCHMARK RESULTS SUMMARY")
    print("-" * 70)
    success_rate = (count / num_requests * 100.0) if num_requests else 0.0
    print(f"Total Requests Completed:   {count} / {num_requests} ({success_rate:.1f}% Success; {failed_requests} failed)")
    print(f"Total Wall Time:            {total_time:.2f} seconds")
    print(f"Throughput:                 {rps:.1f} req/sec (Single Process TestClient)")
    print(f"Min Latency:                {min_lat:.2f} ms")
    print(f"P50 Median Latency:         {p50:.2f} ms")
    print(f"P90 Latency:                {p90:.2f} ms")
    print(f"P95 Latency:                {p95:.2f} ms")
    print(f"P99 Latency:                {p99:.2f} ms")
    print(f"Max Latency:                {max_lat:.2f} ms")
    print(f"Requests Under {threshold_ms}ms Target: {under_target_percentage:.2f}%")
    print("-" * 70)

    if p95 <= threshold_ms:
        print(f">>> P95 IS WITHIN THE CONFIGURED {threshold_ms}ms TARGET <<<")
    else:
        print(f">>> P95 EXCEEDS THE CONFIGURED {threshold_ms}ms TARGET <<<")
    print("=" * 70)


if __name__ == "__main__":
    runs = 300
    if len(sys.argv) > 1:
        runs = int(sys.argv[1])
    run_benchmark(runs)
