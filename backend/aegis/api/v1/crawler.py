import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from aegis.api.v1.auth import require_role
from aegis.models.database import CrawledPage, SiteCrawl, User
from aegis.models.schemas import SiteCrawlRequest
from aegis.services.site_crawler import crawl_site
from aegis.services.storage import get_db

router = APIRouter(prefix="/crawler", tags=["Company Website Crawler"])


def _iso_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _serialize_run(run: SiteCrawl, db: Session, include_pages: bool = False):
    result = {
        "id": run.id,
        "requested_url": run.requested_url,
        "origin": run.origin,
        "status": run.status,
        "max_pages": run.max_pages,
        "pages_discovered": run.pages_discovered,
        "pages_crawled": run.pages_crawled,
        "pages_failed": run.pages_failed,
        "pages_skipped_robots": run.pages_skipped_robots,
        "started_at": _iso_utc(run.started_at),
        "completed_at": _iso_utc(run.completed_at),
    }
    if include_pages:
        pages = db.query(CrawledPage).filter(CrawledPage.crawl_id == run.id).order_by(CrawledPage.fetched_at.asc()).all()
        result["pages"] = [
            {
                "url": page.url,
                "canonical_url": page.canonical_url,
                "http_status": page.http_status,
                "title": page.title,
                "description": page.description,
                "headings": json.loads(page.headings_json or "[]"),
                "internal_links": json.loads(page.internal_links_json or "[]"),
                "text_excerpt": page.text_excerpt,
                "error": page.error,
                "fetched_at": _iso_utc(page.fetched_at),
            }
            for page in pages
        ]
    return result


@router.post("/crawl")
async def start_crawl(
    payload: SiteCrawlRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(["analyst", "auditor"])),
):
    try:
        data = await crawl_site(payload.url, payload.max_pages)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    run = SiteCrawl(
        requested_url=data["requested_url"],
        origin=data["origin"],
        status=data["status"],
        max_pages=payload.max_pages,
        pages_discovered=data["pages_discovered"],
        pages_crawled=data["pages_crawled"],
        pages_failed=data["pages_failed"],
        pages_skipped_robots=data["pages_skipped_robots"],
        completed_at=datetime.now(timezone.utc),
    )
    db.add(run)
    db.flush()
    for page in data["pages"]:
        db.add(CrawledPage(
            crawl_id=run.id,
            url=page["url"],
            canonical_url=page.get("canonical_url"),
            http_status=page.get("http_status"),
            title=page.get("title", "")[:512],
            description=page.get("description", ""),
            headings_json=json.dumps(page.get("headings", [])),
            internal_links_json=json.dumps(page.get("links", [])),
            text_excerpt=page.get("text_excerpt", ""),
            error=page.get("error"),
        ))
    db.commit()
    db.refresh(run)
    return _serialize_run(run, db, include_pages=True)


@router.get("/runs")
def list_crawl_runs(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_role(["analyst", "auditor"])),
):
    runs = db.query(SiteCrawl).order_by(desc(SiteCrawl.started_at)).limit(limit).all()
    return [_serialize_run(run, db) for run in runs]


@router.get("/runs/{run_id}")
def get_crawl_run(
    run_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(["analyst", "auditor"])),
):
    run = db.query(SiteCrawl).filter(SiteCrawl.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Crawl run not found")
    return _serialize_run(run, db, include_pages=True)
