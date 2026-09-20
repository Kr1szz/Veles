import json
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

router = APIRouter(prefix="/verify", tags=["Risk Verification"])


@router.post("/kyc", response_model=RiskEvaluationResponse, status_code=status.HTTP_200_OK)
async def verify_kyc(
    payload: KYCVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Sub-50ms Identity & KYC Risk Engine (Aligned with IDfy OnboardIQ & Privy).
    Executes velocity checks, deterministic rules, Shannon entropy lexical analysis,
    Verhoeff checksum, DPDPA column-level encryption, and immutable audit logging.
    """
    try:
        result = await verification_pipeline.process_kyc_verification(payload, db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification pipeline failed: {str(e)}"
        )


@router.post("/transaction", response_model=RiskEvaluationResponse, status_code=status.HTTP_200_OK)
async def verify_transaction(
    payload: TransactionVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Sub-50ms Real-Time Transaction Risk Engine (Aligned with IDfy OneRisk).
    Executes EWMA anomaly deviation, velocity counters, and fraud heuristic scoring.
    """
    try:
        result = await verification_pipeline.process_transaction_verification(payload, db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transaction pipeline failed: {str(e)}"
        )


@router.get("/records")
def list_verifications(
    entity_type: Optional[str] = Query(None, description="KYC or TRANSACTION"),
    decision: Optional[str] = Query(None, description="APPROVE, REVIEW, REJECT"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
