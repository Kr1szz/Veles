# Benchmarking notes

There is no verified production SLA result checked into this repository. Earlier versions of this document contained fixed latency numbers without reproducible environment details; those figures have been removed.

## What the included script measures

`benchmarks/latency_test.py` sends sequential requests through FastAPI's in-process `TestClient`. It reports wall-clock request latency, throughput, and latency percentiles for that local run. It does not measure a deployed network path, multi-worker throughput, realistic concurrent load, or representative production data.

The script calls the KYC verification endpoint without credentials. This works in the default local demo mode (`AUTH_ENABLED=false`). If authentication is enabled, benchmark credentials need to be added to the script or requests will fail.

## Run a local measurement

```bash
make build-cpp
make benchmark
```

Record the code revision, operating system, CPU, Python version, native-engine status, database configuration, Redis status, request count, and command output with any result you share. Run multiple trials and include warm-up, concurrency, error rate, and percentile methodology.

`SLA_MAX_LATENCY_MS` is a configured decision-pipeline threshold. It does not guarantee that requests meet that threshold. The pipeline's reported `latency_ms` is measured before database persistence and event broadcast, while the benchmark's client timing includes more of the in-process request path. Treat those values as different measurements.
