from fastapi import APIRouter, Depends
from aegis.engine.rule_engine import rule_engine, DISPOSABLE_EMAIL_DOMAINS, FLAGGED_DEVICE_FINGERPRINTS
from aegis.config import settings
from aegis.api.v1.auth import require_role
from aegis.models.database import User

router = APIRouter(prefix="/rules", tags=["Rule Configuration"])


@router.get("")
def get_rule_configurations(_: User = Depends(require_role(["analyst", "auditor"]))):
    """
    Returns active deterministic rules, thresholds, and blacklist counts.
    """
    return {
        "rules": [
            {
                "id": "RULE-VEL-01",
                "name": "KYC IP Velocity Limit",
                "type": "VELOCITY",
                "threshold": f"{settings.VELOCITY_KYC_LIMIT_PER_MIN} attempts/min",
                "action": "FLAG_HIGH_RISK"
            },
            {
                "id": "RULE-VEL-02",
                "name": "Transaction Velocity Limit",
                "type": "VELOCITY",
                "threshold": f"{settings.VELOCITY_TX_LIMIT_PER_MIN} transactions/min",
                "action": "FLAG_HIGH_RISK"
            },
            {
                "id": "RULE-BLK-01",
                "name": "Disposable Email Domain Blacklist",
                "type": "DETERMINISTIC",
                "active_domains_count": len(DISPOSABLE_EMAIL_DOMAINS),
                "action": "HARD_REJECT"
            },
            {
                "id": "RULE-BLK-02",
                "name": "Bot Emulator / Flagged Fingerprint Blacklist",
                "type": "DETERMINISTIC",
                "active_fingerprints_count": len(FLAGGED_DEVICE_FINGERPRINTS),
                "action": "HARD_REJECT"
            },
            {
                "id": "RULE-FMT-01",
                "name": "PAN Indian Format & Entity Code",
                "type": "FORMAT_REGEX",
                "specification": "[A-Z]{5}[0-9]{4}[A-Z]",
                "action": "FLAG_HIGH_RISK"
            },
            {
                "id": "RULE-FMT-02",
                "name": "Aadhaar Verhoeff Dihedral Checksum",
                "type": "ALGORITHMIC",
                "specification": "Verhoeff Checksum (D5 Dihedral Group)",
                "action": "FLAG_HIGH_RISK"
            },
            {
                "id": "RULE-ANOM-01",
                "name": "Shannon Entropy Lexical Anomaly",
                "type": "ENTROPY_ML",
                "high_threshold": settings.SHANNON_ENTROPY_HIGH_THRESHOLD,
                "low_threshold": settings.SHANNON_ENTROPY_LOW_THRESHOLD,
                "action": "DYNAMIC_SCORE_WEIGHT"
            },
            {
                "id": "RULE-ANOM-02",
                "name": "EWMA Transaction Variance Spike",
                "type": "STATISTICAL_EWMA",
                "alpha": settings.EWMA_ALPHA,
                "action": "DYNAMIC_SCORE_WEIGHT"
            }
        ],
        "system_thresholds": {
            "auto_approve_cutoff": settings.RISK_THRESHOLD_AUTO_APPROVE,
            "manual_review_cutoff": settings.RISK_THRESHOLD_MANUAL_REVIEW,
            "sla_max_latency_ms": settings.SLA_MAX_LATENCY_MS
        }
    }
