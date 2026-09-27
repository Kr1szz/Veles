import json
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from aegis.models.schemas import (
    KYCVerificationRequest, TransactionVerificationRequest, RiskEvaluationResponse
)
from aegis.models.database import VerificationRecord
from aegis.engine.pipeline import verification_pipeline
from aegis.services.storage import get_db
from aegis.api.v1.auth import require_role

router = APIRouter(prefix="/verify", tags=["Risk Verification"])
logger = logging.getLogger("aegis.api.verify")


@router.post("/kyc", response_model=RiskEvaluationResponse, status_code=status.HTTP_200_OK)
async def verify_kyc(
    payload: KYCVerificationRequest,
    db: Session = Depends(get_db),
    _: object = Depends(require_role(["analyst", "auditor"]))
):
    """
    Evaluates KYC inputs with configured rules and heuristic anomaly scoring,
    then stores masked/encrypted fields and an application-level hash-linked audit entry.
    """
    if not getattr(payload, "consent_given", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="KYC verification requires explicit consent (consent_given=true) under DPDPA"
        )
    try:
        result = await verification_pipeline.process_kyc_verification(payload, db)
        return result
    except Exception:
        logger.exception("KYC verification pipeline failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Verification could not be completed"
        )


@router.post("/transaction", response_model=RiskEvaluationResponse, status_code=status.HTTP_200_OK)
async def verify_transaction(
    payload: TransactionVerificationRequest,
    db: Session = Depends(get_db),
    _: object = Depends(require_role(["analyst", "auditor"]))
):
    """
    Evaluates transaction inputs with velocity rules and heuristic anomaly scoring.
    """
    try:
        result = await verification_pipeline.process_transaction_verification(payload, db)
        return result
    except Exception:
        logger.exception("Transaction verification pipeline failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Verification could not be completed"
        )


@router.get("/records")
def list_verifications(
    entity_type: Optional[str] = Query(None, description="KYC or TRANSACTION"),
    decision: Optional[str] = Query(None, description="APPROVE, REVIEW, REJECT"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: object = Depends(require_role(["analyst", "auditor"]))
):
    """
    Lists verification records with masked PII for analyst review.
    """
    query = db.query(VerificationRecord)
    if entity_type:
        query = query.filter(VerificationRecord.entity_type == entity_type.upper())
    if decision:
        query = query.filter(VerificationRecord.decision == decision.upper())

    total = query.count()
    records = query.order_by(desc(VerificationRecord.created_at)).offset(offset).limit(limit).all()

    items = []
    for r in records:
        items.append({
            "id": r.id,
            "entity_type": r.entity_type,
            "name_masked": r.full_name_masked,
            "email_masked": r.email_masked,
            "phone_masked": r.phone_masked,
            "id_type": r.id_type,
            "id_masked": r.id_number_masked,
            "amount": r.amount,
            "currency": r.currency,
            "decision": r.decision,
            "risk_score": r.risk_score,
            "latency_ms": r.latency_ms,
            "rules_triggered": json.loads(r.rules_triggered) if r.rules_triggered else [],
            "anomaly_details": json.loads(r.anomaly_details) if r.anomaly_details else {},
            "created_at": r.created_at.isoformat()
        })

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": items
    }


@router.get("/{record_id}")
def get_verification_record(
    record_id: str,
    db: Session = Depends(get_db),
    _: object = Depends(require_role(["analyst", "auditor"]))
):
    r = db.query(VerificationRecord).filter(VerificationRecord.id == record_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Verification record not found")

    return {
        "id": r.id,
        "entity_type": r.entity_type,
        "name_masked": r.full_name_masked,
        "email_masked": r.email_masked,
        "phone_masked": r.phone_masked,
        "id_type": r.id_type,
        "id_masked": r.id_number_masked,
        "amount": r.amount,
        "currency": r.currency,
        "decision": r.decision,
        "risk_score": r.risk_score,
        "latency_ms": r.latency_ms,
        "rules_triggered": json.loads(r.rules_triggered) if r.rules_triggered else [],
        "anomaly_details": json.loads(r.anomaly_details) if r.anomaly_details else {},
        "created_at": r.created_at.isoformat(),
        "reviews": [
            {
                "id": rev.id,
                "analyst": rev.analyst_username,
                "original_decision": rev.original_decision,
                "override_decision": rev.override_decision,
                "notes": rev.review_notes,
                "reviewed_at": rev.reviewed_at.isoformat()
            }
            for rev in r.reviews
        ]
    }
