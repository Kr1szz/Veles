import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from aegis.config import settings
from aegis.core.middleware import SecurityHeadersMiddleware, GlobalRateLimitMiddleware
from aegis.services.storage import init_db
from aegis.engine.cpp_bindings import HAS_CPP_ENGINE
from aegis.api.v1.router import api_router

logging.basicConfig(
    level=logging.getLevelNamesMapping().get(settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("aegis.main")

MAX_BODY_BYTES = 32 * 1024


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.validate_production_secrets()
    logger.info("Initializing Veles Shield Fraud Detection & Verification Pipeline...")
    init_db()
    logger.info(f"C++ Native Anomaly Engine Active: {HAS_CPP_ENGINE}")
    logger.info("Veles Shield API ready to accept requests.")
    yield
    logger.info("Shutting down Veles Shield services.")


docs_enabled = settings.ENABLE_DOCS if settings.ENABLE_DOCS is not None else settings.ENVIRONMENT.lower() != "production"

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Prototype API for verification risk scoring, audit records, and bounded company website crawling.",
    lifespan=lifespan,
    docs_url="/docs" if docs_enabled else None,
    redoc_url="/redoc" if docs_enabled else None,
    openapi_url="/openapi.json" if docs_enabled else None
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(GlobalRateLimitMiddleware)

# CORS Middleware with restricted origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Response-Time-Ms", "X-Request-ID"]
)


@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > MAX_BODY_BYTES:
        return JSONResponse({"detail": "Request payload is too large"}, status_code=413)
    return await call_next(request)


# Mount the versioned API as one composed router.
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "HEALTHY",
        "sla_target": "<50ms"
    }


# Mount Static Frontend if built
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.isdir(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.api_route("/{full_path:path}", methods=["GET", "HEAD"])
    def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            return JSONResponse({"detail": "Not found"}, status_code=404)

        index_file = os.path.join(frontend_dist, "index.html")

        if full_path.startswith("assets/"):
            asset_path = os.path.join(frontend_dist, full_path)
            if os.path.isfile(asset_path):
                return FileResponse(
                    asset_path,
                    headers={"Cache-Control": "public, max-age=31536000, immutable"}
                )

        if os.path.exists(index_file):
            return FileResponse(index_file, headers={"Cache-Control": "no-cache"})
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
