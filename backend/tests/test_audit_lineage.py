import pytest
from aegis.core.audit import ImmutableAuditLedger


def test_audit_ledger_chain_integrity():
    entries = []

    # Block 1
    b1 = ImmutableAuditLedger.create_entry(
        sequence_number=1,
        event_type="KYC_VERIFICATION_EVALUATED",
        entity_id="rec_001",
        actor="SYSTEM",
        action_details={"decision": "APPROVE", "risk_score": 0.12},
        prev_hash=None
    )
    entries.append(b1)

    # Block 2
    b2 = ImmutableAuditLedger.create_entry(
        sequence_number=2,
        event_type="ANALYST_DECISION_OVERRIDE",
        entity_id="rec_001",
        actor="analyst_vikram",
        action_details={"override": "REJECT", "notes": "Suspected stolen ID"},
        prev_hash=b1["entry_hash"]
    )
    entries.append(b2)

    # Block 3
    b3 = ImmutableAuditLedger.create_entry(
        sequence_number=3,
        event_type="DPDPA_DATA_ERASURE",
        entity_id="rec_001",
        actor="dpo_admin",
        action_details={"reason": "User opt-out"},
        prev_hash=b2["entry_hash"]
    )
    entries.append(b3)

    # Verify intact chain
    is_intact, err = ImmutableAuditLedger.verify_chain_integrity(entries)
    assert is_intact is True
    assert err is None


def test_audit_ledger_tamper_detection():
    # Construct 2 blocks
    b1 = ImmutableAuditLedger.create_entry(
        sequence_number=1,
        event_type="TX_EVALUATED",
        entity_id="tx_100",
        actor="SYSTEM",
        action_details={"amount": 5000},
        prev_hash=None
    )
    b2 = ImmutableAuditLedger.create_entry(
        sequence_number=2,
        event_type="TX_EVALUATED",
        entity_id="tx_101",
        actor="SYSTEM",
        action_details={"amount": 9000},
        prev_hash=b1["entry_hash"]
    )

    tampered_entries = [b1.copy(), b2.copy()]
    # Malicious actor tampers with amount in Block 1
    tampered_entries[0]["action_details"] = {"amount": 500}  # changed 5000 to 500

    is_intact, err = ImmutableAuditLedger.verify_chain_integrity(tampered_entries)
    assert is_intact is False
    assert "Hash mismatch at sequence 1" in err


def test_audit_ledger_broken_linkage():
    b1 = ImmutableAuditLedger.create_entry(1, "KYC", "e1", "SYS", {"a": 1}, None)
    b2 = ImmutableAuditLedger.create_entry(2, "KYC", "e2", "SYS", {"b": 2}, b1["entry_hash"])

    tampered_entries = [b1, b2.copy()]
    tampered_entries[1]["prev_hash"] = "fake_hash_12345"

    is_intact, err = ImmutableAuditLedger.verify_chain_integrity(tampered_entries)
    assert is_intact is False
    assert "Broken chain linkage" in err
