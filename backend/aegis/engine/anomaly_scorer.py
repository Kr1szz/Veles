import math
import logging
from typing import Dict, Any, List, Optional
from aegis.engine.cpp_bindings import (
    calculate_shannon_entropy,
    calculate_name_anomaly,
    calculate_ewma_deviation
)
from aegis.config import settings

logger = logging.getLogger("aegis.engine.anomaly")


class AnomalyScorer:
    """
    Shannon Entropy & Statistical Anomaly Scorer.
    Detects synthetic identity creation, keyboard-smashed identities,
    entropy deviations, and anomalous transaction amount spikes.
    """

    def __init__(self):
        self.entropy_high_threshold = settings.SHANNON_ENTROPY_HIGH_THRESHOLD
        self.entropy_low_threshold = settings.SHANNON_ENTROPY_LOW_THRESHOLD

    def score_kyc_payload(
        self,
        full_name: str,
        email: str,
        phone: Optional[str] = None,
        device_fingerprint: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyzes KYC payload for synthetic identity and anomaly indicators.
        Returns detailed anomaly breakdown and composite risk score.
        """
        flags: List[str] = []

        # 1. Full Name Entropy and Structural Analysis
        name_entropy = calculate_shannon_entropy(full_name)
        name_anomaly_score = calculate_name_anomaly(full_name)

        if name_anomaly_score >= 0.40:
            flags.append("HIGH_NAME_STRUCTURAL_ANOMALY")
        if name_entropy > self.entropy_high_threshold:
            flags.append("ABNORMAL_NAME_SHANNON_ENTROPY_HIGH")
        elif len(full_name) > 4 and name_entropy < self.entropy_low_threshold:
            flags.append("ABNORMAL_NAME_SHANNON_ENTROPY_LOW")

        # 2. Email Username Entropy & Randomness
        email_user = email.split("@")[0] if "@" in email else email
        email_entropy = calculate_shannon_entropy(email_user)
        email_anomaly = 0.0

        # Bot-generated emails often have high entropy (e.g. "x87af39d1b@...")
        if len(email_user) >= 8 and email_entropy > 3.6:
            email_anomaly = min(1.0, (email_entropy - 3.4) / 0.8)
            flags.append("SUSPICIOUS_EMAIL_USER_HIGH_ENTROPY")

        # Digits in email username
        digit_count = sum(1 for c in email_user if c.isdigit())
        if len(email_user) > 0 and (digit_count / len(email_user)) > 0.6:
            email_anomaly = max(email_anomaly, 0.45)
            flags.append("EXCESSIVE_DIGITS_IN_EMAIL")

        # 3. Device Fingerprint Randomness/Integrity
        device_anomaly = 0.0
        if device_fingerprint:
            # Check for dummy or spoofed device IDs (e.g. '00000000', '12345678', 'undefined')
            fp_lower = device_fingerprint.lower()
            if fp_lower in {"undefined", "null", "none", "unknown", "test", "device_id"}:
                device_anomaly = 0.80
                flags.append("FLAGGED_DUMMY_DEVICE_FINGERPRINT")
            elif len(set(fp_lower)) <= 2:
                device_anomaly = 0.70
                flags.append("REPETITIVE_DEVICE_FINGERPRINT")

        # Weighted Composite Score
        composite_score = (
            0.50 * name_anomaly_score +
            0.30 * email_anomaly +
            0.20 * device_anomaly
        )
        composite_score = min(1.0, max(0.0, composite_score))

        return {
            "composite_anomaly_score": round(composite_score, 4),
            "name_entropy": round(name_entropy, 3),
            "name_anomaly_score": round(name_anomaly_score, 3),
            "email_entropy": round(email_entropy, 3),
            "email_anomaly_score": round(email_anomaly, 3),
            "device_anomaly_score": round(device_anomaly, 3),
            "anomaly_flags": flags
        }

    def score_transaction_payload(
        self,
        amount: float,
        ewma_mean: float,
        ewma_var: float,
        user_history_count: int,
        device_fingerprint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyzes transaction amount against user's historical EWMA baseline.
        """
        flags: List[str] = []

        # 1. EWMA Statistical Deviation
        ewma_risk = 0.0
        if user_history_count >= 3 and ewma_mean > 0:
            ewma_risk = calculate_ewma_deviation(
                current_val=amount,
                ewma_mean=ewma_mean,
                ewma_var=ewma_var,
                alpha=settings.EWMA_ALPHA
            )
            if ewma_risk >= 0.50:
                flags.append("STATISTICAL_EWMA_AMOUNT_SPIKE")

        # 2. First-Time Large Transaction Heuristic
        elif user_history_count < 3 and amount > 50000.0:
            ewma_risk = 0.65
            flags.append("NEW_ACCOUNT_LARGE_VALUE_ATTEMPT")

        # 3. Device Anomaly
        device_risk = 0.0
        if device_fingerprint:
            fp_lower = device_fingerprint.lower()
            if fp_lower in {"undefined", "null", "none", "unknown", "test"}:
                device_risk = 0.75
                flags.append("FLAGGED_DUMMY_DEVICE_FINGERPRINT")

        composite = max(ewma_risk, device_risk * 0.8)
        return {
            "composite_anomaly_score": round(composite, 4),
            "ewma_risk_score": round(ewma_risk, 3),
            "anomaly_flags": flags
        }


anomaly_scorer = AnomalyScorer()
