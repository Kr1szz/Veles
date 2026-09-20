import pytest


def test_kyc_verification_endpoint_success(client):
    payload = {
        "full_name": "Rohan Mehra",
        "email": "rohan.mehra@gmail.com",
        "phone": "+919876543210",
        "id_type": "PAN",
        "id_number": "ABCPE1234F",
        "country_code": "IN",
        "device_fingerprint": "dev_normal_chrome_v110",
        "ip_address": "103.21.244.2",
        "consent_given": True,
        "consent_purpose": "RBI KYC Verification"
    }

    response = client.post("/api/v1/verify/kyc", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["decision"] == "APPROVE"
    assert data["risk_score"] < 0.30
    assert data["sla_met"] is True
    assert data["latency_ms"] < 50.0  # Must be sub-50ms
    assert "name" in data["masked_identifiers"]
    assert "audit_hash" in data
    assert "X-Response-Time-Ms" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"


def test_kyc_verification_disposable_email_rejection(client):
    payload = {
        "full_name": "Fraud Bot",
        "email": "fraudster@mailinator.com",
        "phone": "+919876543210",
        "id_type": "PAN",
        "id_number": "ABCPE1234F",
        "country_code": "IN",
        "device_fingerprint": "dev_normal_chrome",
        "ip_address": "103.21.244.2",
        "consent_given": True,
        "consent_purpose": "Testing"
    }

    response = client.post("/api/v1/verify/kyc", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "REJECT"
    assert data["risk_score"] >= 0.85
    assert any(r["rule"] == "DISPOSABLE_EMAIL_DOMAIN" for r in data["triggered_rules"])


def test_transaction_verification_endpoint(client):
    # Normal transaction
    payload = {
        "user_id": "usr_9981",
        "amount": 2500.0,
        "currency": "INR",
        "device_fingerprint": "dev_iphone_15",
        "ip_address": "103.21.244.2",
        "user_historical_mean": 2000.0,
        "user_historical_var": 100000.0,
        "user_history_count": 10
    }

    response = client.post("/api/v1/verify/transaction", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "APPROVE"
    assert data["latency_ms"] < 50.0


def test_analyst_review_override_workflow(client, auth_headers):
    # First submit an ambiguous KYC case that falls into REVIEW
    payload = {
        "full_name": "xX Arthur Pendelton Xx",
        "email": "user9988@genericdomain.com",
        "phone": "+919876543210",
        "id_type": "PAN",
        "id_number": "ABCDE1234F",
        "country_code": "IN",
        "device_fingerprint": "dev_unusual",
        "ip_address": "103.21.244.2",
        "consent_given": True,
        "consent_purpose": "Account Onboarding"
    }
    submit_resp = client.post("/api/v1/verify/kyc", json=payload)
    verification_id = submit_resp.json()["verification_id"]

    # Analyst overrides decision to APPROVE
    override_payload = {
        "override_decision": "APPROVE",
        "review_notes": "Verified Aadhaar and PAN documents via video KYC call."
    }
    rev_resp = client.post(
        f"/api/v1/reviews/{verification_id}/override",
        json=override_payload,
        headers=auth_headers
    )
    assert rev_resp.status_code == 200
    rev_data = rev_resp.json()
    assert rev_data["status"] == "success"
    assert rev_data["new_decision"] == "APPROVE"
    assert "audit_hash" in rev_data


def test_dpdpa_audit_chain_verification_endpoint(client):
    # Verify cryptographic integrity of entire DB audit log
    resp = client.post("/api/v1/dpdpa/audit-ledger/verify")
    assert resp.status_code == 200
    data = resp.json()
    assert data["chain_intact"] is True
    assert data["total_blocks_verified"] >= 1


def test_metrics_endpoint(client):
    resp = client.get("/api/v1/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert "latency_percentiles" in data
    assert "decision_distribution" in data
    assert "infrastructure" in data
    assert data["latency_percentiles"]["sla_target_ms"] == 50.0
