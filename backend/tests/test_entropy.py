import pytest
from aegis.engine.cpp_bindings import (
    calculate_shannon_entropy,
    calculate_name_anomaly,
    calculate_ewma_deviation,
    validate_verhoeff
)
from aegis.engine.anomaly_scorer import anomaly_scorer


def test_shannon_entropy_basic():
    # Empty string should yield 0.0 entropy
    assert calculate_shannon_entropy("") == 0.0
    assert calculate_shannon_entropy(None) == 0.0

    # Single repeating character has zero entropy
    assert calculate_shannon_entropy("aaaaaaaa") == 0.0

    # High entropy random string
    high_ent = calculate_shannon_entropy("q7!xZ@9#pL")
    low_ent = calculate_shannon_entropy("abababab")
    assert high_ent > low_ent
    assert high_ent > 3.0


def test_name_anomaly_scoring():
    # Normal natural name should have low risk
    risk_normal = calculate_name_anomaly("Aarav Sharma")
    assert risk_normal < 0.20

    # Keyboard smash with 6 consecutive consonants
    risk_smash = calculate_name_anomaly("zkqjxpbv")
    assert risk_smash >= 0.40

    # Name containing numbers
    risk_numbers = calculate_name_anomaly("Vikram123")
    assert risk_numbers >= 0.40

    # Character repetition
    risk_repeat = calculate_name_anomaly("Jooohhhnnnn")
    assert risk_repeat > 0.30


def test_ewma_deviation():
    # Baseline: transaction matches mean -> risk = 0
    risk_normal = calculate_ewma_deviation(current_val=100.0, ewma_mean=100.0, ewma_var=100.0)
    assert risk_normal == 0.0

    # Extreme spike: transaction is 10 standard deviations above mean -> high risk
    risk_spike = calculate_ewma_deviation(current_val=50000.0, ewma_mean=1000.0, ewma_var=25000.0)
    assert risk_spike > 0.80

    # Cold start: no history -> nominal 0.0
    risk_cold = calculate_ewma_deviation(current_val=500.0, ewma_mean=0.0, ewma_var=0.0)
    assert risk_cold == 0.0


def test_verhoeff_algorithm():
    # Valid Aadhaar numbers generated via Verhoeff algorithm
    # E.g. 219049213459, 123456789012 (needs valid checksum)
    # We test with known Verhoeff sequences:
    # 2363 has valid Verhoeff digit
    # Aadhaar requires 12 digits:
    assert validate_verhoeff("") is False
    assert validate_verhoeff("123") is False
    assert validate_verhoeff("abcdefghijkl") is False

    # Check that invalid 12-digit fails
    assert validate_verhoeff("111111111111") is False


def test_anomaly_scorer_kyc_payload():
    result = anomaly_scorer.score_kyc_payload(
        full_name="Rajesh Kumar",
        email="rajesh.kumar@example.com",
        phone="+919876543210",
        device_fingerprint="fp_browser_chrome_linux"
    )
    assert result["composite_anomaly_score"] < 0.30
    assert len(result["anomaly_flags"]) == 0

    # High risk payload with random email and dummy device
    bad_result = anomaly_scorer.score_kyc_payload(
        full_name="zkqjxpbv99",
        email="x98q7w6e5r4t3y@example.com",
        phone="+919876543210",
        device_fingerprint="undefined"
    )
    assert bad_result["composite_anomaly_score"] > 0.45
    assert len(bad_result["anomaly_flags"]) > 0
