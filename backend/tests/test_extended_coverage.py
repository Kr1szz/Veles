import pytest
from fastapi.testclient import TestClient
from aegis.models.schemas import LoginRequest
from aegis.engine import cpp_bindings
from aegis.core.security import verify_password, hash_password, decode_access_token


def test_auth_login_and_me(client):
    # Test valid login
    resp = client.post("/api/v1/auth/login", json={
        "username": "test_analyst",
        "password": "Password123!"
    })
    assert resp.status_code == 200
    token_data = resp.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # Test /me with token
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == "test_analyst"

    # Test invalid password
    bad_resp = client.post("/api/v1/auth/login", json={
        "username": "test_analyst",
        "password": "WrongPassword"
    })
    assert bad_resp.status_code == 401

    # Test missing / unauthorized
    unauth_resp = client.get("/api/v1/auth/me")
    assert unauth_resp.status_code == 401


def test_records_listing_and_filtering(client):
    # List all records
    resp = client.get("/api/v1/verify/records?limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data

    if data["items"]:
        rec_id = data["items"][0]["id"]
        single_resp = client.get(f"/api/v1/verify/{rec_id}")
        assert single_resp.status_code == 200
        assert single_resp.json()["id"] == rec_id

    # Non-existent record
    not_found = client.get("/api/v1/verify/non_existent_uuid_12345")
    assert not_found.status_code == 404


def test_review_queue_endpoint(client):
    resp = client.get("/api/v1/reviews/queue")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_pending" in data
    assert "items" in data


def test_dpdpa_endpoints(client, auth_headers):
    # Audit ledger query
    ledger_resp = client.get("/api/v1/dpdpa/audit-ledger?limit=10")
    assert ledger_resp.status_code == 200
    assert "total_records" in ledger_resp.json()

    # Consents query
    consents_resp = client.get("/api/v1/dpdpa/consents?limit=10")
    assert consents_resp.status_code == 200
    assert isinstance(consents_resp.json(), list)

    # Erasure API
    erase_resp = client.post(
        "/api/v1/dpdpa/erasure",
        json={"identifier": "test.user@example.com", "reason": "Account Closure"},
        headers=auth_headers
    )
    assert erase_resp.status_code == 200
    assert erase_resp.json()["status"] == "success"


def test_cpp_engine_pure_python_fallbacks(monkeypatch):
    """
    Simulate environment where libveles.so is not present to test pure Python fallbacks.
    """
    original_lib = cpp_bindings._lib
    original_fn_shannon = cpp_bindings._fn_shannon
    original_fn_name = cpp_bindings._fn_name
    original_fn_ewma = cpp_bindings._fn_ewma
    original_fn_verhoeff = cpp_bindings._fn_verhoeff
    try:
        cpp_bindings._lib = None
        cpp_bindings._fn_shannon = None
        cpp_bindings._fn_name = None
        cpp_bindings._fn_ewma = None
        cpp_bindings._fn_verhoeff = None

        # Test pure python entropy
        ent = cpp_bindings.calculate_shannon_entropy("Hello World")
        assert ent > 2.0
        assert cpp_bindings.calculate_shannon_entropy("") == 0.0

        # Test pure python name anomaly
        risk = cpp_bindings.calculate_name_anomaly("zxvbnm99")
        assert risk > 0.40

        # Test pure python EWMA deviation
        ewma_dev = cpp_bindings.calculate_ewma_deviation(10000.0, 1000.0, 40000.0)
        assert ewma_dev > 0.50

        # Test pure python Verhoeff
        assert cpp_bindings.validate_verhoeff("123456789012") is False
    finally:
        cpp_bindings._lib = original_lib
        cpp_bindings._fn_shannon = original_fn_shannon
        cpp_bindings._fn_name = original_fn_name
        cpp_bindings._fn_ewma = original_fn_ewma
        cpp_bindings._fn_verhoeff = original_fn_verhoeff


def test_rules_configuration_endpoint(client):
    resp = client.get("/api/v1/rules")
    assert resp.status_code == 200
    data = resp.json()
    assert "rules" in data
    assert "system_thresholds" in data
    assert len(data["rules"]) >= 6


def test_health_check_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "HEALTHY"
    assert data["sla_target"] == "<50ms"
