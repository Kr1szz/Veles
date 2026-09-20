import pytest
from aegis.core.security import (
    encrypt_pii,
    decrypt_pii,
    mask_pii_field,
    compute_blind_index
)
from aegis.services.storage import StorageService
from aegis.models.database import VerificationRecord


def test_pii_encryption_and_decryption():
    secret_pan = "ABCDE1234F"
    encrypted = encrypt_pii(secret_pan)
    assert encrypted != secret_pan
    assert len(encrypted) > 20

    decrypted = decrypt_pii(encrypted)
    assert decrypted == secret_pan

    # None and empty handling
    assert encrypt_pii(None) is None
    assert decrypt_pii(None) is None


def test_pii_masking():
    # Aadhaar masking
    assert mask_pii_field("aadhaar", "987654321098") == "XXXX-XXXX-1098"
    assert mask_pii_field("aadhaar_number", "9876 5432 1098") == "XXXX-XXXX-1098"

    # PAN masking
    assert mask_pii_field("pan", "ABCDE1234F") == "ABCDE****F"

    # Email masking
    assert mask_pii_field("email", "john.doe@example.com") == "j******e@example.com"
    assert mask_pii_field("email", "ab@example.com") == "a*@example.com"

    # Phone masking
    masked_phone = mask_pii_field("phone", "+919876543210")
    assert "98765" not in masked_phone
    assert masked_phone.endswith("10")


def test_blind_indexing():
    # Deterministic index for exact-match searches
    idx1 = compute_blind_index("ABCDE1234F")
    idx2 = compute_blind_index("abcde1234f ")
    assert idx1 == idx2
    assert len(idx1) == 64  # SHA-256 hex string

    idx_different = compute_blind_index("XYZWE9999K")
    assert idx1 != idx_different


def test_dpdpa_erasure_workflow(db_session):
    # Save a verification record
    rec, audit = StorageService.save_kyc_verification(
        db=db_session,
        full_name="Sunita Rao",
        email="sunita.rao@example.com",
        phone="+919811122233",
        id_type="PAN",
        id_number="ABCDE9999Z",
        ip_address="103.20.10.5",
        device_fingerprint="fp_test_device",
        decision="APPROVE",
        risk_score=0.15,
        latency_ms=12.4,
        rules_triggered=[],
        anomaly_breakdown={},
        consent_given=True,
        consent_purpose="KYC Onboarding"
    )

    # Verify encrypted fields exist
    assert rec.full_name_encrypted is not None
    assert decrypt_pii(rec.full_name_encrypted) == "Sunita Rao"

    # Execute DPDPA Erasure for this individual
    count = StorageService.execute_dpdpa_erasure(
        db=db_session,
        identifier="ABCDE9999Z",
        actor="dpo_admin",
        reason="User requested account deletion"
    )
    assert count == 1

    # Reload record from DB
    updated = db_session.query(VerificationRecord).filter(VerificationRecord.id == rec.id).first()
    assert updated.full_name_encrypted is None
    assert updated.email_encrypted is None
    assert updated.phone_encrypted is None
    assert updated.id_number_encrypted is None
    assert updated.full_name_masked == "[ERASED_UNDER_DPDPA]"
