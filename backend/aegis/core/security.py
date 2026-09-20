import hmac
import hashlib
import re
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
import jwt
import bcrypt

from aegis.config import settings


# Initialize Fernet symmetric encryption cipher
_cipher = Fernet(settings.AEGIS_ENCRYPTION_KEY.encode("utf-8"))


def encrypt_pii(plaintext: Optional[str]) -> Optional[str]:
    """
    DPDPA 2023 Compliance: Encrypt sensitive personal identifiable data at rest.
    Uses authenticated AES symmetric encryption.
    """
    if not plaintext:
        return None
    try:
        return _cipher.encrypt(plaintext.encode("utf-8")).decode("utf-8")
    except Exception as e:
        raise ValueError(f"Failed to encrypt PII: {e}") from e


def decrypt_pii(ciphertext: Optional[str]) -> Optional[str]:
    """
    Decrypts encrypted PII. Restricted to authorized audit/analyst workflows.
    """
    if not ciphertext:
        return None
    try:
        return _cipher.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except Exception as e:
        raise ValueError(f"Failed to decrypt PII: {e}") from e


def compute_blind_index(value: Optional[str]) -> Optional[str]:
    """
    Computes a cryptographic HMAC-SHA256 blind index.
    Allows exact-match lookups (e.g. duplicate identity detection)
    without storing plaintext or decrypting the entire database.
    """
    if not value:
        return None
    normalized = value.strip().upper()
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        normalized.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def mask_pii_field(field_name: str, value: Optional[str]) -> str:
    """
    Redacts sensitive personal information for UI displays and audit logs.
    """
    if not value:
        return "N/A"

    name_lower = field_name.lower()
    raw = value.strip()

    # Mask Aadhaar (12 digits): "XXXX-XXXX-1234"
    if "aadhaar" in name_lower or (len(raw.replace(" ", "").replace("-", "")) == 12 and raw.replace(" ", "").replace("-", "").isdigit()):
        digits = raw.replace(" ", "").replace("-", "")
        if len(digits) == 12:
            return f"XXXX-XXXX-{digits[-4:]}"

    # Mask PAN: "ABCDE****F"
    if "pan" in name_lower:
        cleaned = raw.replace(" ", "").upper()
        if len(cleaned) == 10:
            return f"{cleaned[:5]}****{cleaned[-1]}"

    # Mask Email: "j***e@domain.com"
    if "email" in name_lower or "@" in raw:
        if "@" in raw:
            local, domain = raw.split("@", 1)
            if len(local) <= 2:
                masked_local = f"{local[:1]}*"
            else:
                masked_local = f"{local[:1]}{'*' * (len(local) - 2)}{local[-1]}"
            return f"{masked_local}@{domain}"

    # Mask Phone: "+91-XXXXX-12"
    if "phone" in name_lower or "mobile" in name_lower:
        cleaned = re.sub(r"[^\d+]", "", raw)
        if len(cleaned) >= 10:
            return f"{cleaned[:4]}{'X' * (len(cleaned) - 6)}{cleaned[-2:]}"

    # Fallback generic masking
    if len(raw) <= 4:
        return "****"
    return f"{raw[:2]}{'*' * (len(raw) - 4)}{raw[-2:]}"


# Password Hashing & Verification using bcrypt
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


# JWT Token Management
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"iat": now, "exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError as e:
        raise ValueError(f"Invalid or expired token: {e}") from e
