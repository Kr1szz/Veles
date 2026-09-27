import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple


class ImmutableAuditLedger:
    """
    Application-level SHA-256 hash-linked audit log; this is not immutable storage.
    Ensures transactional lineage and tamper-evident history for every risk decision.
    """

    GENESIS_HASH = "0" * 64

    @staticmethod
    def calculate_entry_hash(
        sequence_number: int,
        timestamp: str,
        event_type: str,
        entity_id: str,
        actor: str,
        action_details: Dict[str, Any],
        prev_hash: str
    ) -> str:
        """
        Computes SHA-256 hash chaining previous entry hash with canonical JSON payload.
        """
        payload_str = json.dumps(action_details, sort_keys=True, separators=(",", ":"))
        raw = f"{sequence_number}|{timestamp}|{event_type}|{entity_id}|{actor}|{payload_str}|{prev_hash}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @classmethod
    def create_entry(
        cls,
        sequence_number: int,
        event_type: str,
        entity_id: str,
        actor: str,
        action_details: Dict[str, Any],
        prev_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates a hash-linked audit log entry.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        previous = prev_hash or cls.GENESIS_HASH
        entry_hash = cls.calculate_entry_hash(
            sequence_number=sequence_number,
            timestamp=timestamp,
            event_type=event_type,
            entity_id=entity_id,
            actor=actor,
            action_details=action_details,
            prev_hash=previous
        )

        return {
            "sequence_number": sequence_number,
            "timestamp": timestamp,
            "event_type": event_type,
            "entity_id": entity_id,
            "actor": actor,
            "action_details": action_details,
            "prev_hash": previous,
            "entry_hash": entry_hash
        }

    @classmethod
    def verify_chain_integrity(cls, entries: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
        """
        Validates cryptographic integrity across the entire sequence of audit logs.
        Returns (True, None) if intact, or (False, error_reason) if tampered.
        """
        if not entries:
            return True, None

        expected_prev_hash = cls.GENESIS_HASH

        for i, entry in enumerate(entries):
            seq = entry.get("sequence_number", i + 1)
            ts = entry.get("timestamp")
            etype = entry.get("event_type")
            eid = entry.get("entity_id")
            actor = entry.get("actor")
            details = entry.get("action_details")
            prev_h = entry.get("prev_hash")
            recorded_hash = entry.get("entry_hash")

            if prev_h != expected_prev_hash:
                return False, f"Broken chain linkage at sequence {seq}: expected prev_hash {expected_prev_hash}, found {prev_h}"

            recomputed_hash = cls.calculate_entry_hash(
                sequence_number=seq,
                timestamp=ts,
                event_type=etype,
                entity_id=eid,
                actor=actor,
                action_details=details,
                prev_hash=prev_h
            )

            if recomputed_hash != recorded_hash:
                return False, f"Hash mismatch at sequence {seq}: entry has been tampered with!"

            expected_prev_hash = recorded_hash

        return True, None
