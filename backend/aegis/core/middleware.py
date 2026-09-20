import time
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("aegis.middleware")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Applies strict production security headers and latency profiling.
    Ensures sub-50ms SLA tracking and protects against XSS, clickjacking, MIME sniffing.
    """

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        start_time = time.perf_counter()

        response: Response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        # Performance & SLA tracking header
        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"
        response.headers["X-Request-ID"] = request_id

        # Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"

        # Production CSP
        csp = (
            "default-src 'self'; "
            "img-src 'self' data:; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp

        # Log slow requests exceeding SLA
        if duration_ms > 50.0 and not request.url.path.startswith("/docs"):
            logger.warning(
                f"[SLA Breach] {request.method} {request.url.path} took {duration_ms:.2f}ms (>50ms SLA)"
            )

        return response
