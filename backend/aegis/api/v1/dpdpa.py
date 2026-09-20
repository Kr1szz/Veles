import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc

from aegis.models.schemas import DataErasureRequest
from aegis.models.database import AuditLog, ConsentRecord, User
from aegis.services.storage import get_db, StorageService
from aegis.core.audit import ImmutableAuditLedger
from aegis.api.v1.auth import get_current_user

router = APIRouter(prefix="/dpdpa", tags=["DPDPA Privacy & Audit Ledger"])


@router.get("/audit-ledger")
def get_audit_ledger(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Returns immutable audit logs with SHA-256 hash chaining details.
    """
    query = db.query(AuditLog)
    total = query.count()
    logs = query.order_by(desc(AuditLog.sequence_number)).offset(offset).limit(limit).all()

    items = []
    for log in logs:
        items.append({
            "sequence_number": log.sequence_number,
            "timestamp": log.timestamp,
            "event_type": log.event_type,
            "entity_id": log.entity_id,
            "actor": log.actor,
            "action_details": json.loads(log.action_details) if log.action_details else {},
            "prev_hash": log.prev_hash,
            "entry_hash": log.entry_hash
        })

    return {
        "total_records": total,
        "items": items
    }


@router.get("/audit-ledger/verify")
@router.post("/audit-ledger/verify")
def verify_audit_ledger_integrity(db: Session = Depends(get_db)):
    """
    Cryptographically verifies the SHA-256 chain integrity of the entire audit log.
    Ensures zero tampering, deletions, or post-facto alterations.
    """
    logs = db.query(AuditLog).order_by(asc(AuditLog.sequence_number)).all()
    entries = []
    for log in logs:
        entries.append({
            "sequence_number": log.sequence_number,
            "timestamp": log.timestamp,
            "event_type": log.event_type,
            "entity_id": log.entity_id,
            "actor": log.actor,
            "action_details": json.loads(log.action_details) if log.action_details else {},
            "prev_hash": log.prev_hash,
            "entry_hash": log.entry_hash
        })

    is_intact, error_reason = ImmutableAuditLedger.verify_chain_integrity(entries)

    return {
        "chain_intact": is_intact,
        "total_blocks_verified": len(entries),
        "genesis_hash": ImmutableAuditLedger.GENESIS_HASH,
        "latest_hash": entries[-1]["entry_hash"] if entries else None,
        "error": error_reason
    }


@router.get("/consents")
def list_consents(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    DPDPA Consent Ledger tracking Purpose Limitation & Statutory Retention.
    """
    records = db.query(ConsentRecord).order_by(desc(ConsentRecord.granted_at)).limit(limit).all()
    return [
        {
            "id": r.id,
            "principal_hash": r.principal_blind_index[:16] + "...",
            "purpose": r.purpose,
            "consent_status": r.consent_status,
            "granted_at": r.granted_at.isoformat(),
            "retention_period_days": r.retention_period_days
        }
        for r in records
    ]


@router.post("/erasure")
def request_erasure(
    payload: DataErasureRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    DPDPA Right to Erasure / Forgotten.
    Wipes encrypted personal data while retaining cryptographic audit ledger hashes.
    """
    scrubbed_count = StorageService.execute_dpdpa_erasure(
        db=db,
        identifier=payload.identifier,
        actor=current_user.username,
        reason=payload.reason
    )

    return {
        "status": "success",
        "records_erased": scrubbed_count,
        "reason": payload.reason,
        "actor": current_user.username
    }
