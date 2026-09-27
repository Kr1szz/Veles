import re
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict


class KYCVerificationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str = Field(..., min_length=2, max_length=120, description="Full legal name of the individual")
    email: str = Field(..., min_length=5, max_length=120, description="Contact email address")
    phone: Optional[str] = Field(None, min_length=7, max_length=20, description="E.164 phone number")
    id_type: Optional[Literal["PAN", "AADHAAR", "PASSPORT", "VOTER_ID"]] = Field(None, description="Identity Document Type")
    id_number: Optional[str] = Field(None, min_length=5, max_length=30, description="Official ID number")
    country_code: str = Field("IN", min_length=2, max_length=3, description="ISO 3166-1 country code")
    device_fingerprint: Optional[str] = Field(None, max_length=128)
    ip_address: Optional[str] = Field(None, max_length=45)
    consent_given: bool = Field(..., description="DPDPA 2023: Explicit consent from data principal")
    consent_purpose: str = Field("Identity Verification & Fraud Prevention under RBI KYC Master Direction", max_length=256)

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        clean = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", clean):
            raise ValueError("Invalid email format")
        return clean

    @field_validator("full_name")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        clean = v.strip()
        if len(clean) < 2:
            raise ValueError("Full name must be at least 2 characters long")
        return clean


class TransactionVerificationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(..., min_length=1, max_length=64, description="Unique account identifier")
    amount: float = Field(..., gt=0.0, description="Transaction amount in specified currency")
    currency: str = Field("INR", min_length=3, max_length=4)
    device_fingerprint: Optional[str] = Field(None, max_length=128)
    ip_address: Optional[str] = Field(None, max_length=45)
    user_historical_mean: float = Field(0.0, ge=0.0, description="EWMA historical mean amount")
    user_historical_var: float = Field(0.0, ge=0.0, description="EWMA historical variance")
    user_history_count: int = Field(0, ge=0, description="Number of past transactions")


class RiskEvaluationResponse(BaseModel):
    verification_id: str
    entity_type: str
    decision: Literal["APPROVE", "REVIEW", "REJECT"]
    risk_score: float = Field(..., ge=0.0, le=1.0)
    latency_ms: float
    sla_met: bool
    triggered_rules: List[Dict[str, Any]]
    anomaly_breakdown: Dict[str, Any]
    masked_identifiers: Dict[str, str]
    audit_hash: str
    timestamp: str


class AnalystReviewRequest(BaseModel):
    override_decision: Literal["APPROVE", "REJECT", "ESCALATE"]
    review_notes: str = Field(..., min_length=5, max_length=1000)


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
    expires_in_minutes: int


class DataErasureRequest(BaseModel):
    identifier: str = Field(..., description="Email, PAN, or Aadhaar number of data principal")
    reason: str = Field("Right to be Forgotten under DPDPA 2023", max_length=256)


class SiteCrawlRequest(BaseModel):
    url: str = Field(..., min_length=8, max_length=2048)
    max_pages: int = Field(20, ge=1, le=50)


class SystemMetricsResponse(BaseModel):
    uptime_seconds: float
    total_evaluations: int
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    approvals_count: int
    reviews_count: int
    rejects_count: int
    active_sliding_window_keys: int
    cpp_engine_accelerated: bool
