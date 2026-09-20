import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(64), unique=True, nullable=False, index=True)
    hashed_password = Column(String(256), nullable=False)
    role = Column(String(32), nullable=False, default="analyst")  # analyst, admin, auditor
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class VerificationRecord(Base):
    __tablename__ = "verification_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    entity_type = Column(String(32), nullable=False, index=True)  # KYC or TRANSACTION
    
    # Encrypted PII Fields (DPDPA 2023 Compliance)
    full_name_encrypted = Column(Text, nullable=True)
    full_name_masked = Column(String(128), nullable=True)
    
    email_encrypted = Column(Text, nullable=True)
    email_masked = Column(String(128), nullable=True)
    
    phone_encrypted = Column(Text, nullable=True)
    phone_masked = Column(String(64), nullable=True)
    
    id_type = Column(String(32), nullable=True)  # PAN, AADHAAR, PASSPORT
    id_number_encrypted = Column(Text, nullable=True)
    id_number_masked = Column(String(64), nullable=True)
    
    # Cryptographic Blind Index (HMAC-SHA256) for deduplication without decrypting
    id_blind_index = Column(String(64), nullable=True, index=True)
    email_blind_index = Column(String(64), nullable=True, index=True)

    # Transaction specific
    amount = Column(Float, nullable=True)
    currency = Column(String(8), nullable=True, default="INR")
    
    # Network & Device Attributes
    ip_address = Column(String(45), nullable=True, index=True)
    device_fingerprint = Column(String(128), nullable=True, index=True)
    
    # Risk Decision & Metrics
    decision = Column(String(16), nullable=False, index=True)  # APPROVE, REVIEW, REJECT
    risk_score = Column(Float, nullable=False)
    latency_ms = Column(Float, nullable=False)
    
    # Serialized JSON audit breakdowns
    rules_triggered = Column(Text, nullable=True)
    anomaly_details = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    reviews = relationship("AnalystReview", back_populates="verification", cascade="all, delete-orphan")


class AnalystReview(Base):
    __tablename__ = "analyst_reviews"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    verification_id = Column(String(36), ForeignKey("verification_records.id"), nullable=False, index=True)
    analyst_username = Column(String(64), nullable=False)
    original_decision = Column(String(16), nullable=False)
    override_decision = Column(String(16), nullable=False)  # APPROVE, REJECT, ESCALATE
    review_notes = Column(Text, nullable=False)
    reviewed_at = Column(DateTime, default=utc_now, nullable=False)

    verification = relationship("VerificationRecord", back_populates="reviews")


class AuditLog(Base):
    """
    Cryptographically chained immutable ledger.
    """
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    sequence_number = Column(Integer, unique=True, nullable=False, index=True)
    timestamp = Column(String(36), nullable=False)
    event_type = Column(String(64), nullable=False, index=True)
    entity_id = Column(String(36), nullable=False, index=True)
    actor = Column(String(64), nullable=False)
    action_details = Column(Text, nullable=False)
    prev_hash = Column(String(64), nullable=False)
    entry_hash = Column(String(64), unique=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class ConsentRecord(Base):
    """
    DPDPA 2023 Purpose Limitation and Consent Record Ledger.
    """
    __tablename__ = "consent_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    principal_blind_index = Column(String(64), nullable=False, index=True)
    purpose = Column(String(256), nullable=False)
    consent_status = Column(String(32), nullable=False, default="GRANTED")  # GRANTED, REVOKED, EXPIRED
    granted_at = Column(DateTime, default=utc_now, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    retention_period_days = Column(Integer, default=1825, nullable=False)  # 5 years statutory retention
