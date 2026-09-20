import json
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import create_engine, desc, func
from sqlalchemy.orm import sessionmaker, Session

from aegis.config import settings
from aegis.models.database import (
    Base, User, VerificationRecord, AnalystReview, AuditLog, ConsentRecord
)
from aegis.core.security import encrypt_pii, decrypt_pii, mask_pii_field, compute_blind_index
from aegis.core.audit import ImmutableAuditLedger

logger = logging.getLogger("aegis.services.storage")

# Configure database engine
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initializes schema. User provisioning is an explicit administrator task."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency for database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class StorageService:
    """
    Data Access Layer handling DPDPA encryption, blind indexing,
    and immutable hash-chained audit logging.
    """

    @staticmethod
    def log_audit_event(
        db: Session,
        event_type: str,
        entity_id: str,
        actor: str,
        action_details: Dict[str, Any]
    ) -> AuditLog:
        """
        Appends an entry to the cryptographic hash chain.
        """
        last_log = db.query(AuditLog).order_by(desc(AuditLog.sequence_number)).first()
        next_seq = (last_log.sequence_number + 1) if last_log else 1
        prev_hash = last_log.entry_hash if last_log else ImmutableAuditLedger.GENESIS_HASH

        entry_data = ImmutableAuditLedger.create_entry(
            sequence_number=next_seq,
            event_type=event_type,
            entity_id=entity_id,
            actor=actor,
            action_details=action_details,
            prev_hash=prev_hash
        )

        audit_entry = AuditLog(
            sequence_number=entry_data["sequence_number"],
            timestamp=entry_data["timestamp"],
            event_type=entry_data["event_type"],
            entity_id=entry_data["entity_id"],
            actor=entry_data["actor"],
            action_details=json.dumps(entry_data["action_details"]),
            prev_hash=entry_data["prev_hash"],
            entry_hash=entry_data["entry_hash"]
        )
        db.add(audit_entry)
        db.flush()
        return audit_entry

    @classmethod
    def save_kyc_verification(
        cls,
        db: Session,
        full_name: str,
        email: str,
        phone: Optional[str],
        id_type: Optional[str],
        id_number: Optional[str],
        ip_address: Optional[str],
        device_fingerprint: Optional[str],
        decision: str,
        risk_score: float,
        latency_ms: float,
        rules_triggered: List[Dict[str, Any]],
        anomaly_breakdown: Dict[str, Any],
        consent_given: bool,
        consent_purpose: str
    ) -> Tuple[VerificationRecord, AuditLog]:
        """
        Persists KYC verification with column-level encryption & immutable audit log.
        """
        # Encrypt sensitive PII for DPDPA compliance
        full_name_enc = encrypt_pii(full_name)
        email_enc = encrypt_pii(email)
        phone_enc = encrypt_pii(phone)
        id_enc = encrypt_pii(id_number)

        # Generate masked representations for UI & logs
        full_name_msk = mask_pii_field("name", full_name)
        email_msk = mask_pii_field("email", email)
        phone_msk = mask_pii_field("phone", phone)
        id_msk = mask_pii_field(id_type or "id", id_number)

        # Generate HMAC blind index for queryability without plaintext exposure
        id_blind = compute_blind_index(id_number)
        email_blind = compute_blind_index(email)

        rec = VerificationRecord(
            entity_type="KYC",
            full_name_encrypted=full_name_enc,
            full_name_masked=full_name_msk,
            email_encrypted=email_enc,
            email_masked=email_msk,
            phone_encrypted=phone_enc,
            phone_masked=phone_msk,
            id_type=id_type,
            id_number_encrypted=id_enc,
            id_number_masked=id_msk,
            id_blind_index=id_blind,
            email_blind_index=email_blind,
            ip_address=ip_address,
            device_fingerprint=device_fingerprint,
            decision=decision,
            risk_score=risk_score,
            latency_ms=latency_ms,
            rules_triggered=json.dumps(rules_triggered),
            anomaly_details=json.dumps(anomaly_breakdown)
        )
        db.add(rec)
        db.flush()

        # Record Consent in DPDPA Ledger
        if consent_given:
            consent = ConsentRecord(
                principal_blind_index=id_blind or email_blind or "unknown",
                purpose=consent_purpose,
                consent_status="GRANTED"
            )
            db.add(consent)

        # Append to Immutable Audit Ledger
        audit_entry = cls.log_audit_event(
            db=db,
            event_type="KYC_VERIFICATION_EVALUATED",
            entity_id=rec.id,
            actor="SYSTEM_ENGINE",
            action_details={
                "decision": decision,
                "risk_score": risk_score,
                "latency_ms": latency_ms,
                "rules_triggered_count": len(rules_triggered),
                "id_type": id_type,
                "id_masked": id_msk,
                "email_masked": email_msk
            }
        )

        db.commit()
        db.refresh(rec)
        return rec, audit_entry

    @classmethod
    def save_transaction_verification(
        cls,
        db: Session,
        user_id: str,
        amount: float,
        currency: str,
        ip_address: Optional[str],
        device_fingerprint: Optional[str],
        decision: str,
        risk_score: float,
        latency_ms: float,
        rules_triggered: List[Dict[str, Any]],
        anomaly_breakdown: Dict[str, Any]
    ) -> Tuple[VerificationRecord, AuditLog]:
        """
        Persists financial transaction risk assessment.
        """
        user_blind = compute_blind_index(user_id)

        rec = VerificationRecord(
            entity_type="TRANSACTION",
            id_blind_index=user_blind,
            id_number_masked=mask_pii_field("user_id", user_id),
            amount=amount,
            currency=currency,
            ip_address=ip_address,
            device_fingerprint=device_fingerprint,
            decision=decision,
            risk_score=risk_score,
            latency_ms=latency_ms,
            rules_triggered=json.dumps(rules_triggered),
            anomaly_details=json.dumps(anomaly_breakdown)
        )
        db.add(rec)
        db.flush()

        audit_entry = cls.log_audit_event(
            db=db,
            event_type="TRANSACTION_RISK_EVALUATED",
            entity_id=rec.id,
            actor="SYSTEM_ENGINE",
            action_details={
                "decision": decision,
                "risk_score": risk_score,
                "amount": amount,
                "currency": currency,
                "latency_ms": latency_ms,
                "rules_triggered_count": len(rules_triggered)
            }
        )

        db.commit()
        db.refresh(rec)
        return rec, audit_entry

    @classmethod
    def apply_analyst_review(
        cls,
        db: Session,
        verification_id: str,
        analyst_username: str,
        override_decision: str,
        review_notes: str
    ) -> Tuple[VerificationRecord, AnalystReview, AuditLog]:
        """
        Records human-in-the-loop analyst review and decision override.
        """
        rec = db.query(VerificationRecord).filter(VerificationRecord.id == verification_id).first()
        if not rec:
            raise ValueError("Verification record not found")
        if rec.decision != "REVIEW":
            raise ValueError("Only records awaiting review can be overridden")

        original_dec = rec.decision
        rec.decision = override_decision

        review = AnalystReview(
            verification_id=rec.id,
            analyst_username=analyst_username,
            original_decision=original_dec,
            override_decision=override_decision,
            review_notes=review_notes
        )
        db.add(review)
        db.flush()

        # Immutable Audit Event for Decision Override
        audit_entry = cls.log_audit_event(
            db=db,
            event_type="ANALYST_DECISION_OVERRIDE",
            entity_id=rec.id,
            actor=analyst_username,
            action_details={
                "original_decision": original_dec,
                "override_decision": override_decision,
                "notes": review_notes
            }
        )

        db.commit()
        db.refresh(rec)
        db.refresh(review)
        return rec, review, audit_entry

    @classmethod
    def execute_dpdpa_erasure(
        cls,
        db: Session,
        identifier: str,
        actor: str,
        reason: str
    ) -> int:
        """
        DPDPA 2023 Right to Erasure / Forgotten:
        Scans matching blind index and securely scrubs encrypted PII fields.
        Retains anonymized audit hashes to satisfy legal AML/KYC audit requirements.
        """
        blind = compute_blind_index(identifier)
        records = db.query(VerificationRecord).filter(
            (VerificationRecord.id_blind_index == blind) |
            (VerificationRecord.email_blind_index == blind)
        ).all()

        count = len(records)
        for r in records:
            r.full_name_encrypted = None
            r.email_encrypted = None
            r.phone_encrypted = None
            r.id_number_encrypted = None
            r.full_name_masked = "[ERASED_UNDER_DPDPA]"
            r.email_masked = "[ERASED_UNDER_DPDPA]"
            r.phone_masked = "[ERASED_UNDER_DPDPA]"
            r.id_number_masked = "[ERASED_UNDER_DPDPA]"

            cls.log_audit_event(
                db=db,
                event_type="DPDPA_DATA_ERASURE",
                entity_id=r.id,
                actor=actor,
                action_details={
                    "reason": reason,
                    "erased_fields": ["full_name", "email", "phone", "id_number"]
                }
            )

        db.commit()
        return count
