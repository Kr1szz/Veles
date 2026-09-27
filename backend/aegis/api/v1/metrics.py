import time
import hashlib
import json
import asyncio
import math
from typing import Optional
from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from aegis.models.database import VerificationRecord, User
from aegis.services.storage import get_db
from aegis.engine.cpp_bindings import HAS_CPP_ENGINE
from aegis.core.rate_limiter import rate_limiter
from aegis.api.v1.auth import require_role
from aegis.config import settings

router = APIRouter(prefix="/metrics", tags=["Metrics & Processing Time"])
START_TIME = time.time()

_CACHE_LOCK = asyncio.Lock()
_CACHE_TTL_SECONDS = 5.0
_cached_payload: Optional[dict] = None
_cached_etag: Optional[str] = None
_cached_timestamp: float = 0.0


@router.get("")
async def get_system_metrics(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(["analyst", "auditor"])),
):
    """
    Returns stored decision counts, observed latency percentiles, and configuration status,
    decision distributions, and acceleration engine health.
    Cached for 5 seconds with ETag support for efficient polling.
    """
    global _cached_payload, _cached_etag, _cached_timestamp

    now = time.time()
    if _cached_payload is not None and (now - _cached_timestamp) < _CACHE_TTL_SECONDS:
        client_etag = request.headers.get("if-none-match")
        if client_etag and client_etag == _cached_etag:
            return Response(status_code=status.HTTP_304_NOT_MODIFIED)
        resp = JSONResponse(content=_cached_payload)
        resp.headers["ETag"] = _cached_etag or ""
        resp.headers["Cache-Control"] = "private, max-age=5"
        return resp

    async with _CACHE_LOCK:
        # Re-check inside lock
        if _cached_payload is not None and (time.time() - _cached_timestamp) < _CACHE_TTL_SECONDS:
            client_etag = request.headers.get("if-none-match")
            if client_etag and client_etag == _cached_etag:
                return Response(status_code=status.HTTP_304_NOT_MODIFIED)
            resp = JSONResponse(content=_cached_payload)
            resp.headers["ETag"] = _cached_etag or ""
            resp.headers["Cache-Control"] = "private, max-age=5"
            return resp

        # 1. SQL Aggregate counts by decision
        counts_by_decision = dict(
            db.query(VerificationRecord.decision, func.count(VerificationRecord.id))
            .group_by(VerificationRecord.decision)
            .all()
        )

        total = sum(counts_by_decision.values())
        approvals = counts_by_decision.get("APPROVE", 0)
        reviews = counts_by_decision.get("REVIEW", 0)
        rejects = counts_by_decision.get("REJECT", 0)
        escalates = counts_by_decision.get("ESCALATE", 0)

        # 2. Windowed percentiles over recent records (up to 5,000)
        recent_latencies = [
            r[0] for r in (
                db.query(VerificationRecord.latency_ms)
                .order_by(desc(VerificationRecord.created_at))
                .limit(5000)
                .all()
            )
            if r[0] is not None
        ]

        if recent_latencies:
            recent_latencies.sort()
            n = len(recent_latencies)
            p50 = recent_latencies[max(0, math.ceil(n * 0.50) - 1)]
            p95 = recent_latencies[max(0, math.ceil(n * 0.95) - 1)]
            p99 = recent_latencies[max(0, math.ceil(n * 0.99) - 1)]
        else:
            p50, p95, p99 = 0.0, 0.0, 0.0

        active_keys_count = await rate_limiter.active_key_count()
        redis_connected = await rate_limiter.is_redis_connected()

        payload = {
            "uptime_seconds": round(time.time() - START_TIME, 1),
            "total_evaluations": total,
            "latency_percentiles": {
                "p50_ms": round(p50, 2),
                "p95_ms": round(p95, 2),
                "p99_ms": round(p99, 2),
                "sample_size": len(recent_latencies),
                "sample_limit": 5000,
                "sla_target_ms": settings.SLA_MAX_LATENCY_MS,
                "target_met": (p95 <= settings.SLA_MAX_LATENCY_MS) if total > 0 else None
            },
            "decision_distribution": {
                "approve": approvals,
                "review": reviews,
                "reject": rejects,
                "escalate": escalates,
                "approval_rate": round(approvals / total, 3) if total > 0 else 0.0,
                "rejection_rate": round(rejects / total, 3) if total > 0 else 0.0,
                "review_rate": round(reviews / total, 3) if total > 0 else 0.0
            },
            "infrastructure": {
                "cpp_engine_accelerated": HAS_CPP_ENGINE,
                "active_velocity_keys": active_keys_count,
                "redis_connected": redis_connected
            }
        }

        # Compute ETag
        etag = f'"{hashlib.md5(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()}"'

        _cached_payload = payload
        _cached_etag = etag
        _cached_timestamp = time.time()

        client_etag = request.headers.get("if-none-match")
        if client_etag and client_etag == etag:
            return Response(status_code=status.HTTP_304_NOT_MODIFIED)

        resp = JSONResponse(content=payload)
        resp.headers["ETag"] = etag
        resp.headers["Cache-Control"] = "private, max-age=5"
        return resp
