import base64
import logging
import os
import secrets
from typing import List, Optional
from cryptography.fernet import Fernet
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("aegis.config")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "Veles Shield"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Security: Secrets & Token Configuration
    # In production, these should be supplied via environment variables
    # Deployment secrets are deliberately never committed to source control.
    SECRET_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours
    ALGORITHM: str = "HS256"

    # API documentation exposure. Defaults to disabled in production, enabled otherwise.
    ENABLE_DOCS: Optional[bool] = None

    # Cookie & host hardening
    COOKIE_SECURE: Optional[bool] = None
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "testserver"]

    # Demo operator accounts (seeded only outside production)
    DEMO_SEED_ENABLED: bool = True
    DEMO_ANALYST_USERNAME: str = "demo.analyst"
    DEMO_AUDITOR_USERNAME: str = "demo.auditor"
    DEMO_PASSWORD: Optional[str] = None

    # DPDPA Column-Level Encryption Key (32-byte urlsafe base64 for Fernet / AES)
    AEGIS_ENCRYPTION_KEY: str = ""
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

    @field_validator("SECRET_KEY", mode="before")
    @classmethod
    def validate_secret_key(cls, value: object) -> str:
        raw = value or ""
        if raw:
            return str(raw)
        if os.environ.get("ENVIRONMENT", "development").lower() == "production":
            return ""
        logger.warning(
            "SECRET_KEY is unset; generating an ephemeral development key. "
            "Set SECRET_KEY in production (validate_production_secrets will hard-fail otherwise)."
        )
        return secrets.token_hex(32)

    @field_validator("DEBUG", mode="before")
    @classmethod
    def normalize_debug_flag(cls, value: object) -> bool:
        if isinstance(value, str) and value.lower() in {"release", "production", "prod"}:
            return False
        return value

    @field_validator("AEGIS_ENCRYPTION_KEY", mode="before")
    @classmethod
    def validate_encryption_key(cls, v: str) -> str:
        override = os.environ.get("VELES_ENCRYPTION_KEY")
        target = override or v
        if not target:
            # Prevent plaintext storage during local use. Production startup
            # rejects ephemeral keys through validate_production_secrets().
            return Fernet.generate_key().decode("ascii")
        try:
            decoded = base64.urlsafe_b64decode(target)
            if len(decoded) != 32:
                # If padding or length differs, re-encode a 32-byte key
                raise ValueError("Encryption key must decode to exactly 32 bytes")
        except Exception as exc:
            raise ValueError("AEGIS_ENCRYPTION_KEY must be a URL-safe base64 32-byte Fernet key") from exc
        return target

    def validate_production_secrets(self) -> None:
        if self.ENVIRONMENT.lower() == "production":
            if len(self.SECRET_KEY) < 32:
                raise RuntimeError("SECRET_KEY must be supplied by the production secret manager (minimum 32 characters).")
            if not (os.environ.get("VELES_ENCRYPTION_KEY") or os.environ.get("AEGIS_ENCRYPTION_KEY")):
                raise RuntimeError("VELES_ENCRYPTION_KEY must be supplied by the production secret manager.")


settings = Settings()
