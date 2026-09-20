import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from aegis.config import settings
from aegis.core.middleware import SecurityHeadersMiddleware
from aegis.services.storage import init_db
from aegis.engine.cpp_bindings import HAS_CPP_ENGINE
from aegis.api.v1.auth import router as auth_router
from aegis.api.v1.verify import router as verify_router
from aegis.api.v1.reviews import router as reviews_router
from aegis.api.v1.dpdpa import router as dpdpa_router
from aegis.api.v1.rules import router as rules_router
from aegis.api.v1.metrics import router as metrics_router
from aegis.api.v1.events import router as events_router
from aegis.core.rate_limiter import rate_limiter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("aegis.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Veles Shield Fraud Detection & Verification Pipeline...")
    init_db()
    logger.info(f"C++ Native Anomaly Engine Active: {HAS_CPP_ENGINE}")
    logger.info("Veles Shield ready to accept high-throughput verification requests.")
    yield
    logger.info("Shutting down Veles Shield services.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Real-Time High-Throughput Fraud Detection & Verification Pipeline (IDfy OnboardIQ, OneRisk, Privy)",
    lifespan=lifespan
)

# Apply Security Headers & SLA Timing Profiling
app.add_middleware(SecurityHeadersMiddleware)

# CORS Middleware with restricted origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Response-Time-Ms", "X-Request-ID"]
)

# Mount API Routers under /api/v1
api_v1_prefix = "/api/v1"
app.include_router(auth_router, prefix=api_v1_prefix)
app.include_router(verify_router, prefix=api_v1_prefix)
app.include_router(reviews_router, prefix=api_v1_prefix)
app.include_router(dpdpa_router, prefix=api_v1_prefix)
app.include_router(rules_router, prefix=api_v1_prefix)
app.include_router(metrics_router, prefix=api_v1_prefix)
app.include_router(events_router, prefix=api_v1_prefix)


@app.get("/health", tags=["Health"])
async def health_check():
    redis_active = await rate_limiter.is_redis_connected()
    return {
        "status": "HEALTHY",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "cpp_engine_active": HAS_CPP_ENGINE,
        "redis_active": redis_active,
        "sla_target": "<50ms"
    }


# Mount Static Frontend if built
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.isdir(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        index_file = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return JSONResponse({"status": "Veles Shield API Operational", "docs": "/docs"})
else:
    @app.get("/")
    def root_api():
        return {
            "message": "Veles Shield High-Throughput Fraud Detection Pipeline is running.",
            "docs": "/docs",
            "health": "/health",
            "api_version": "v1"
        }
