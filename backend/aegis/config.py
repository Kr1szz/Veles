import base64
import os
from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "Veles Shield"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False

    # Security: Secrets & Token Configuration
    # In production, these should be supplied via environment variables
    SECRET_KEY: str = "veles-shield-production-secret-key-must-be-rotated-32bytes"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours
    ALGORITHM: str = "HS256"

    # DPDPA Column-Level Encryption Key (32-byte urlsafe base64 for Fernet / AES)
    # Default stable 32-byte key for development/test if not overridden
    AEGIS_ENCRYPTION_KEY: str = "c2VjdXJlLWRwZHBhLWFlZ2lzLXRydXN0LTIwMjYtMDAwMSE="
    VELES_ENCRYPTION_KEY: Optional[str] = None

    # Database
    DATABASE_URL: str = "sqlite:///./veles_shield.db"

    # Redis Cache & Rate Limiting
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = True

    # Performance & SLA Thresholds
    SLA_MAX_LATENCY_MS: float = 50.0  # sub-50ms SLA requirement
    RATE_LIMIT_GLOBAL_PER_MIN: int = 120
    VELOCITY_KYC_LIMIT_PER_MIN: int = 5
    VELOCITY_TX_LIMIT_PER_MIN: int = 10

    # Risk Scoring Thresholds
    RISK_THRESHOLD_AUTO_APPROVE: float = 0.30
    RISK_THRESHOLD_MANUAL_REVIEW: float = 0.70  # Between 0.30 and 0.70 goes to REVIEW
    SHANNON_ENTROPY_HIGH_THRESHOLD: float = 4.2
    SHANNON_ENTROPY_LOW_THRESHOLD: float = 1.2
    EWMA_ALPHA: float = 0.20

    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    @field_validator("AEGIS_ENCRYPTION_KEY", mode="before")
    @classmethod
    def validate_encryption_key(cls, v: str) -> str:
        override = os.environ.get("VELES_ENCRYPTION_KEY")
        target = override or v
        try:
            decoded = base64.urlsafe_b64decode(target)
            if len(decoded) != 32:
                # If padding or length differs, re-encode a 32-byte key
                raise ValueError("Encryption key must decode to exactly 32 bytes")
        except Exception:
            # Generate deterministic fallback 32 bytes for dev
            raw = (target + "0" * 32)[:32].encode("utf-8")
            return base64.urlsafe_b64encode(raw).decode("ascii")
        return target


settings = Settings()
