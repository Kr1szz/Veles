import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from aegis.models.schemas import AnalystReviewRequest
from aegis.models.database import VerificationRecord, User
from aegis.services.storage import get_db, StorageService
from aegis.api.v1.auth import require_role

router = APIRouter(prefix="/reviews", tags=["Analyst Review Queue"])
logger = logging.getLogger("aegis.api.reviews")


@router.get("/queue")
def get_review_queue(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(require_role(["analyst", "auditor"]))
):
    """
    Returns verifications flagged with REVIEW status for human-in-the-loop analyst decisions.
    """
    query = db.query(VerificationRecord).filter(VerificationRecord.decision == "REVIEW")
    total = query.count()
    records = query.order_by(desc(VerificationRecord.created_at)).offset(offset).limit(limit).all()

    items = []
    for r in records:
        items.append({
            "id": r.id,
            "entity_type": r.entity_type,
            "name_masked": r.full_name_masked,
            "email_masked": r.email_masked,
            "id_type": r.id_type,
            "id_masked": r.id_number_masked,
            "amount": r.amount,
            "currency": r.currency,
            "risk_score": r.risk_score,
            "latency_ms": r.latency_ms,
            "rules_triggered": json.loads(r.rules_triggered) if r.rules_triggered else [],
            "anomaly_details": json.loads(r.anomaly_details) if r.anomaly_details else {},
            "created_at": r.created_at.isoformat()
        })

    return {
        "total_pending": total,
        "items": items
    }


@router.post("/{verification_id}/override")
def override_decision(
    verification_id: str,
    payload: AnalystReviewRequest,
    current_user: User = Depends(require_role(["analyst"])),
    db: Session = Depends(get_db)
):
    """
    Allows authorized analysts to manually override a decision (APPROVE/REJECT/ESCALATE).
    Logs the action into the cryptographic immutable audit ledger.
    """
    try:
        rec, review, audit_log = StorageService.apply_analyst_review(
            db=db,
            verification_id=verification_id,
            analyst_username=current_user.username,
            override_decision=payload.override_decision,
            review_notes=payload.review_notes
        )
        return {
            "status": "success",
            "verification_id": rec.id,
            "new_decision": rec.decision,
            "override_id": review.id,
            "audit_hash": audit_log.entry_hash,
            "analyst": current_user.username,
            "timestamp": review.reviewed_at.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        logger.exception("Analyst override failed")
        raise HTTPException(status_code=500, detail="Override could not be recorded")
