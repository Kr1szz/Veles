import re
import ipaddress
import logging
from typing import Dict, Any, List, Optional, Tuple
from aegis.core.rate_limiter import rate_limiter
from aegis.engine.cpp_bindings import validate_verhoeff
from aegis.config import settings

logger = logging.getLogger("aegis.engine.rules")

# Disposable & Temporary Email Domains
DISPOSABLE_EMAIL_DOMAINS = {
    "mailinator.com",
    "10minutemail.com",
    "tempmail.com",
    "guerrillamail.com",
    "sharklasers.com",
    "dispostable.com",
    "yopmail.com",
    "trashmail.com",
    "getairmail.com",
    "fakeinbox.com",
    "throwawaymail.com",
    "temp-mail.org",
    "inboxkitten.com"
}

# Known Flagged / High-Risk IP subnets (Simulated blacklist / TOR exit nodes / compromised proxy ranges)
FLAGGED_IP_NETWORKS = [
    ipaddress.ip_network("198.51.100.0/24"),  # Testnet-2 / simulated bad subnet
    ipaddress.ip_network("203.0.113.0/24"),   # Testnet-3 / simulated botnet
    ipaddress.ip_network("185.220.101.0/24"), # Public known TOR exit relay block
]

# Flagged Device Fingerprints (Stolen / Bot emulator fingerprints)
FLAGGED_DEVICE_FINGERPRINTS = {
    "dev_bot_emulator_x86",
    "fingerprint_suspicious_device_999",
    "rooted_android_bluestacks_v1",
    "automated_puppeteer_agent"
}

# Regex for Indian PAN Card (5 letters, 4 digits, 1 letter)
PAN_REGEX = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")


class RuleEngine:
    """
    Deterministic Verification Rule Engine for KYC and Financial Transactions.
    Evaluates hard constraints, blacklists, format compliance, and velocity spikes.
    """

    def __init__(self):
        self.disposable_domains = set(DISPOSABLE_EMAIL_DOMAINS)
        self.flagged_devices = set(FLAGGED_DEVICE_FINGERPRINTS)

    def is_disposable_email(self, email: str) -> bool:
        if not email or "@" not in email:
            return True
        domain = email.split("@")[-1].lower().strip()
        return domain in self.disposable_domains

    def is_flagged_ip(self, ip_str: Optional[str]) -> bool:
        if not ip_str:
            return False
        try:
            ip_obj = ipaddress.ip_address(ip_str.strip())
            for net in FLAGGED_IP_NETWORKS:
                if ip_obj in net:
                    return True
        except ValueError:
            return False
        return False

    def validate_pan(self, pan: Optional[str]) -> Tuple[bool, Optional[str]]:
        if not pan:
            return False, "PAN_MISSING"
        cleaned = pan.strip().upper()
        if not PAN_REGEX.match(cleaned):
            return False, "INVALID_PAN_FORMAT"
        # 4th character indicates PAN holder entity type:
        # P = Individual, C = Company, H = HUF, F = Firm, A = AOP, T = Trust, B = BOI, L = Local Auth, J = Artificial Juridical, G = Govt
        valid_entity_types = {"P", "C", "H", "F", "A", "T", "B", "L", "J", "G"}
        if cleaned[3] not in valid_entity_types:
            return False, "INVALID_PAN_ENTITY_CODE"
        return True, None

    def validate_aadhaar(self, aadhaar: Optional[str]) -> Tuple[bool, Optional[str]]:
        if not aadhaar:
            return False, "AADHAAR_MISSING"
        cleaned = re.sub(r"[\s-]", "", aadhaar)
        if len(cleaned) != 12 or not cleaned.isdigit():
            return False, "INVALID_AADHAAR_LENGTH"
        if not validate_verhoeff(cleaned):
            return False, "AADHAAR_VERHOEFF_CHECKSUM_FAILED"
        return True, None

    async def evaluate_kyc_rules(
        self,
        full_name: str,
        email: str,
        phone: Optional[str],
        ip_address: Optional[str],
        device_fingerprint: Optional[str],
        id_type: Optional[str],
        id_number: Optional[str],
        country_code: str = "IN",
        ip_country: Optional[str] = "IN"
    ) -> Dict[str, Any]:
        """
        Executes all deterministic rules against a KYC application.
        """
        triggered_rules: List[Dict[str, Any]] = []
        hard_reject = False

        # 1. IP Velocity Check
        if ip_address:
            allowed, count, retry_after = await rate_limiter.check_velocity(
                key=f"velocity:ip:{ip_address}",
                limit=settings.VELOCITY_KYC_LIMIT_PER_MIN,
                window_seconds=60
            )
            if not allowed:
                triggered_rules.append({
                    "rule": "VELOCITY_EXCEEDED_IP",
                    "severity": "HIGH",
                    "weight": 0.40,
                    "detail": f"Exceeded {settings.VELOCITY_KYC_LIMIT_PER_MIN} KYC attempts/min from IP ({count} attempts)"
                })

        # 2. Disposable Email Domain Check
        if self.is_disposable_email(email):
            hard_reject = True
            triggered_rules.append({
                "rule": "DISPOSABLE_EMAIL_DOMAIN",
                "severity": "CRITICAL",
                "weight": 0.85,
                "detail": f"Email domain in disposable/burner provider blacklist: {email}"
            })

        # 3. Flagged IP / TOR Network Check
        if ip_address and self.is_flagged_ip(ip_address):
            triggered_rules.append({
                "rule": "FLAGGED_HIGH_RISK_IP",
                "severity": "HIGH",
                "weight": 0.60,
                "detail": f"IP address belongs to a known proxy/TOR exit pool: {ip_address}"
            })

        # 4. Flagged Device Fingerprint Check
        if device_fingerprint and device_fingerprint in self.flagged_devices:
            hard_reject = True
            triggered_rules.append({
                "rule": "FLAGGED_DEVICE_FINGERPRINT",
                "severity": "CRITICAL",
                "weight": 0.90,
                "detail": "Device fingerprint associated with automated bot emulator"
            })

        # 5. Geolocation / Country Mismatch
        if ip_country and country_code and ip_country != country_code:
            triggered_rules.append({
                "rule": "GEO_LOCATION_MISMATCH",
                "severity": "MEDIUM",
                "weight": 0.25,
                "detail": f"Document issued for country {country_code}, but request originated from IP country {ip_country}"
            })

        # 6. ID Document Verification (PAN / Aadhaar)
        if id_type and id_number:
            id_type_upper = id_type.upper()
            if id_type_upper == "PAN":
                is_valid, err = self.validate_pan(id_number)
                if not is_valid:
                    triggered_rules.append({
                        "rule": f"PAN_VALIDATION_ERROR_{err}",
                        "severity": "HIGH",
                        "weight": 0.50,
                        "detail": f"PAN check failed: {err}"
                    })
            elif id_type_upper == "AADHAAR":
                is_valid, err = self.validate_aadhaar(id_number)
                if not is_valid:
                    triggered_rules.append({
                        "rule": f"AADHAAR_VALIDATION_ERROR_{err}",
                        "severity": "HIGH",
                        "weight": 0.50,
                        "detail": f"Aadhaar check failed: {err}"
                    })

        # Compute Rule-Based Risk Contribution
        rule_risk_score = 0.0
        for r in triggered_rules:
            rule_risk_score += r["weight"]
        rule_risk_score = min(1.0, rule_risk_score)

        return {
            "triggered_rules": triggered_rules,
            "rule_risk_score": round(rule_risk_score, 4),
            "hard_reject": hard_reject,
            "rule_count": len(triggered_rules)
        }

    async def evaluate_transaction_rules(
        self,
        user_id: str,
        amount: float,
        currency: str,
        ip_address: Optional[str],
        device_fingerprint: Optional[str]
    ) -> Dict[str, Any]:
        """
        Executes deterministic transaction velocity & blacklist checks.
        """
        triggered_rules: List[Dict[str, Any]] = []

        # 1. User Transaction Velocity Check
        allowed, count, retry_after = await rate_limiter.check_velocity(
            key=f"velocity:tx:user:{user_id}",
            limit=settings.VELOCITY_TX_LIMIT_PER_MIN,
            window_seconds=60
        )
        if not allowed:
            triggered_rules.append({
                "rule": "VELOCITY_EXCEEDED_TRANSACTIONS",
                "severity": "HIGH",
                "weight": 0.45,
                "detail": f"User exceeded {settings.VELOCITY_TX_LIMIT_PER_MIN} transactions/min ({count} attempts)"
            })

        # 2. Flagged IP Check
        if ip_address and self.is_flagged_ip(ip_address):
            triggered_rules.append({
                "rule": "TRANSACTION_FROM_FLAGGED_IP",
                "severity": "HIGH",
                "weight": 0.55,
                "detail": f"Transaction initiated from flagged network: {ip_address}"
            })

        # 3. Flagged Device Check
        if device_fingerprint and device_fingerprint in self.flagged_devices:
            triggered_rules.append({
                "rule": "TRANSACTION_FROM_FLAGGED_DEVICE",
                "severity": "CRITICAL",
                "weight": 0.85,
                "detail": "Device fingerprint associated with compromised device"
            })

        rule_risk_score = min(1.0, sum(r["weight"] for r in triggered_rules))

        return {
            "triggered_rules": triggered_rules,
            "rule_risk_score": round(rule_risk_score, 4),
            "rule_count": len(triggered_rules)
        }


rule_engine = RuleEngine()
