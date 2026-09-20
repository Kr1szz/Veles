import time
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from aegis.models.database import VerificationRecord
from aegis.services.storage import get_db
from aegis.engine.cpp_bindings import HAS_CPP_ENGINE
from aegis.core.rate_limiter import rate_limiter

router = APIRouter(prefix="/metrics", tags=["Metrics & SLA Telemetry"])
START_TIME = time.time()


@router.get("")
def get_system_metrics(db: Session = Depends(get_db)):
    """
    Returns real-time SLA metrics, P50/P95/P99 latency calculations,
    decision distributions, and acceleration engine health.
    """
    records = db.query(VerificationRecord.latency_ms, VerificationRecord.decision).all()
    total = len(records)

    latencies = sorted([r[0] for r in records if r[0] is not None])
    p50 = latencies[int(len(latencies) * 0.50)] if latencies else 0.0
    p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0.0
    p99 = latencies[int(len(latencies) * 0.99)] if latencies else 0.0

    approvals = sum(1 for r in records if r[1] == "APPROVE")
    reviews = sum(1 for r in records if r[1] == "REVIEW")
    rejects = sum(1 for r in records if r[1] == "REJECT")

    active_keys_count = len(rate_limiter._memory_store)

    return {
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_evaluations": total,
        "latency_percentiles": {
            "p50_ms": round(p50, 2),
            "p95_ms": round(p95, 2),
            "p99_ms": round(p99, 2),
            "sla_target_ms": 50.0,
            "sla_compliant": (p95 <= 50.0) if total > 0 else True
        },
        "decision_distribution": {
            "approve": approvals,
            "review": reviews,
            "reject": rejects,
            "approval_rate": round(approvals / total, 3) if total > 0 else 0.0,
            "rejection_rate": round(rejects / total, 3) if total > 0 else 0.0,
            "review_rate": round(reviews / total, 3) if total > 0 else 0.0
        },
        "infrastructure": {
            "cpp_engine_accelerated": HAS_CPP_ENGINE,
            "active_velocity_keys": active_keys_count,
            "redis_connected": rate_limiter._redis_available
        }
    }
