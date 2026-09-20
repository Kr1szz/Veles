import pytest
from aegis.engine.rule_engine import rule_engine


def test_disposable_email_detection():
    assert rule_engine.is_disposable_email("user@mailinator.com") is True
    assert rule_engine.is_disposable_email("attacker@tempmail.com") is True
    assert rule_engine.is_disposable_email("fraud@10minutemail.com") is True
    assert rule_engine.is_disposable_email("legit.user@gmail.com") is False
    assert rule_engine.is_disposable_email("employee@idfy.com") is False


def test_pan_format_validation():
    # Valid individual PAN: 5 uppercase letters (4th is 'P'), 4 digits, 1 uppercase letter
    valid_pan = "ABCPE1234F"
    is_valid, err = rule_engine.validate_pan(valid_pan)
    assert is_valid is True
    assert err is None

    # Valid company PAN (4th letter is 'C')
    valid_company = "AAACC1234D"
    is_valid, err = rule_engine.validate_pan(valid_company)
    assert is_valid is True

    # Invalid length
    is_valid, err = rule_engine.validate_pan("ABCD1234F")
    assert is_valid is False
    assert err == "INVALID_PAN_FORMAT"

    # Invalid 4th character entity code ('Z' is not valid)
    is_valid, err = rule_engine.validate_pan("ABCDZ1234F")
    assert is_valid is False
    assert err == "INVALID_PAN_ENTITY_CODE"


def test_flagged_ip_check():
    # Simulated TOR / Testnet-2 IP
    assert rule_engine.is_flagged_ip("198.51.100.45") is True
    # Clean domestic IP
    assert rule_engine.is_flagged_ip("103.21.244.2") is False
    # Invalid IP string
    assert rule_engine.is_flagged_ip("not_an_ip") is False


@pytest.mark.asyncio
async def test_kyc_rule_evaluation():
    from aegis.core.rate_limiter import rate_limiter
    await rate_limiter.reset()

    # Normal request
    eval_result = await rule_engine.evaluate_kyc_rules(
        full_name="Priya Patel",
        email="priya.patel@gmail.com",
        phone="+919876543210",
        ip_address="103.21.244.2",
        device_fingerprint="fp_device_safe_android",
        id_type="PAN",
        id_number="ABCPE1234F"
    )
    assert eval_result["hard_reject"] is False
    assert eval_result["rule_risk_score"] == 0.0

    # Disposable email should trigger hard reject
    disposable_eval = await rule_engine.evaluate_kyc_rules(
        full_name="Priya Patel",
        email="priya@mailinator.com",
        phone="+919876543210",
        ip_address="103.21.244.2",
        device_fingerprint="fp_device_safe_android",
        id_type="PAN",
        id_number="ABCDE1234F"
    )
    assert disposable_eval["hard_reject"] is True
    assert any(r["rule"] == "DISPOSABLE_EMAIL_DOMAIN" for r in disposable_eval["triggered_rules"])


@pytest.mark.asyncio
async def test_transaction_rule_evaluation():
    eval_result = await rule_engine.evaluate_transaction_rules(
        user_id="user_88291",
        amount=1500.0,
        currency="INR",
        ip_address="103.21.244.2",
        device_fingerprint="fp_device_safe"
    )
    assert eval_result["rule_count"] == 0
    assert eval_result["rule_risk_score"] == 0.0
