from fastapi import APIRouter

from aegis.api.v1.auth import router as auth_router
from aegis.api.v1.crawler import router as crawler_router
from aegis.api.v1.dpdpa import router as dpdpa_router
from aegis.api.v1.events import router as events_router
from aegis.api.v1.metrics import router as metrics_router
from aegis.api.v1.reviews import router as reviews_router
from aegis.api.v1.rules import router as rules_router
from aegis.api.v1.verify import router as verify_router

api_router = APIRouter()

for route in (
    auth_router,
    verify_router,
    reviews_router,
    dpdpa_router,
    rules_router,
    metrics_router,
    events_router,
    crawler_router,
):
    api_router.include_router(route)
