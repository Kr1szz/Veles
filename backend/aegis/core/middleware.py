import time
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from aegis.config import settings
from aegis.core.rate_limiter import rate_limiter

logger = logging.getLogger("aegis.middleware")


def get_client_ip(request: Request) -> str:
    """Best-effort real client IP: honors single-hop X-Forwarded-For, falls back to socket peer."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


class GlobalRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Enforces the global per-IP sliding window across all API endpoints.
    Uses the real client IP (not client-supplied fields) to prevent key spoofing.
    """

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api/") and request.method != "OPTIONS":
            client_ip = get_client_ip(request)
            allowed, _count, retry_after = await rate_limiter.check_velocity(
                key=f"global:{client_ip}",
                limit=settings.RATE_LIMIT_GLOBAL_PER_MIN,
                window_seconds=60
            )
            if not allowed:
                return JSONResponse(
                    {"detail": "Rate limit exceeded, retry later"},
                    status_code=429,
                    headers={"Retry-After": f"{max(1, int(retry_after))}"}
                )
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Applies response security headers and records request latency.
    """

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        start_time = time.perf_counter()

        response: Response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        # Request timing headers
        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"
        response.headers["X-Request-ID"] = request_id

        # Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Production CSP: no inline scripts; inline styles kept for React style props.
        csp = (
            "default-src 'self'; "
            "img-src 'self' data:; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp

        # Ensure authenticated/real-time endpoints are never cached
        if (
            request.method in {"GET", "HEAD"}
            and (
                request.url.path.startswith("/api/")
                or request.url.path == "/index.html"
            )
            and "/assets/" not in request.url.path
        ):
            if "Cache-Control" not in response.headers:
                response.headers["Cache-Control"] = "no-store"

        # Log requests that exceed the configured latency target.
        if duration_ms > settings.SLA_MAX_LATENCY_MS and not request.url.path.startswith("/docs"):
            logger.warning(
                f"[Latency target exceeded] {request.method} {request.url.path} took {duration_ms:.2f}ms (>{settings.SLA_MAX_LATENCY_MS}ms)"
            )

        return response
