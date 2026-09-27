import time
import asyncio
import logging
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session

from aegis.config import settings
from aegis.models.schemas import (
    KYCVerificationRequest, TransactionVerificationRequest, RiskEvaluationResponse
)
from aegis.engine.rule_engine import rule_engine
from aegis.engine.anomaly_scorer import anomaly_scorer
from aegis.services.storage import StorageService
from aegis.services.event_stream import event_broadcaster

logger = logging.getLogger("aegis.engine.pipeline")


class VerificationPipeline:
    """
    High-Throughput Risk Engine Pipeline.
    Evaluates payloads and reports processing time against the configured target.
    """

    @classmethod
    async def process_kyc_verification(
        cls,
        payload: KYCVerificationRequest,
        db: Session
    ) -> RiskEvaluationResponse:
        start_time = time.perf_counter()

        # Rule evaluation is async; the synchronous anomaly score is computed before it is awaited.
        rule_eval_task = rule_engine.evaluate_kyc_rules(
            full_name=payload.full_name,
            email=payload.email,
            phone=payload.phone,
            ip_address=payload.ip_address,
            device_fingerprint=payload.device_fingerprint,
            id_type=payload.id_type,
            id_number=payload.id_number,
            country_code=payload.country_code
        )

        # Anomaly scoring (CPU fast bound via C++ shared library)
        anomaly_results = anomaly_scorer.score_kyc_payload(
            full_name=payload.full_name,
            email=payload.email,
            phone=payload.phone,
            device_fingerprint=payload.device_fingerprint
        )

        rule_results = await rule_eval_task

        # Combine deterministic rules and statistical entropy anomaly score
        hard_reject = rule_results.get("hard_reject", False)
        rule_score = rule_results.get("rule_risk_score", 0.0)
        anomaly_score = anomaly_results.get("composite_anomaly_score", 0.0)

        if hard_reject:
            decision = "REJECT"
            final_risk = max(0.85, (rule_score + anomaly_score) / 2.0)
        else:
            # Weighted ensemble: 60% deterministic rule evidence, 40% anomaly/entropy evidence
            final_risk = min(1.0, 0.60 * rule_score + 0.40 * anomaly_score)
            if final_risk <= settings.RISK_THRESHOLD_AUTO_APPROVE:
                decision = "APPROVE"
            elif final_risk >= settings.RISK_THRESHOLD_MANUAL_REVIEW:
                decision = "REJECT"
            else:
                decision = "REVIEW"

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        sla_met = elapsed_ms <= settings.SLA_MAX_LATENCY_MS

        # Persist selected encrypted fields and an application-level audit entry.
        rec, audit_entry = StorageService.save_kyc_verification(
            db=db,
            full_name=payload.full_name,
            email=payload.email,
            phone=payload.phone,
            id_type=payload.id_type,
            id_number=payload.id_number,
            ip_address=payload.ip_address,
            device_fingerprint=payload.device_fingerprint,
            decision=decision,
            risk_score=round(final_risk, 4),
            latency_ms=round(elapsed_ms, 2),
            rules_triggered=rule_results.get("triggered_rules", []),
            anomaly_breakdown=anomaly_results,
            consent_given=payload.consent_given,
            consent_purpose=payload.consent_purpose
        )

        # Broadcast live event for real-time dashboard monitoring
        event_payload = {
            "id": rec.id,
            "type": "KYC",
            "name": rec.full_name_masked,
            "email": rec.email_masked,
            "id_type": rec.id_type or "N/A",
            "id_masked": rec.id_number_masked or "N/A",
            "decision": decision,
            "risk_score": round(final_risk, 4),
            "latency_ms": round(elapsed_ms, 2),
            "rules_count": len(rule_results.get("triggered_rules", [])),
            "audit_hash": audit_entry.entry_hash[:16] + "...",
            "timestamp": audit_entry.timestamp
        }
        await event_broadcaster.broadcast(event_payload)

        return RiskEvaluationResponse(
            verification_id=rec.id,
            entity_type="KYC",
            decision=decision,
            risk_score=round(final_risk, 4),
            latency_ms=round(elapsed_ms, 2),
            sla_met=sla_met,
            triggered_rules=rule_results.get("triggered_rules", []),
            anomaly_breakdown=anomaly_results,
            masked_identifiers={
                "name": rec.full_name_masked or "",
                "email": rec.email_masked or "",
                "phone": rec.phone_masked or "",
                "id_number": rec.id_number_masked or ""
            },
            audit_hash=audit_entry.entry_hash,
            timestamp=audit_entry.timestamp
        )

    @classmethod
    async def process_transaction_verification(
        cls,
        payload: TransactionVerificationRequest,
        db: Session
    ) -> RiskEvaluationResponse:
        start_time = time.perf_counter()

        # Rule evaluation (velocity, blacklist)
        rule_eval_task = rule_engine.evaluate_transaction_rules(
            user_id=payload.user_id,
            amount=payload.amount,
            currency=payload.currency,
            ip_address=payload.ip_address,
            device_fingerprint=payload.device_fingerprint
        )

        # Anomaly scoring (EWMA deviation)
        anomaly_results = anomaly_scorer.score_transaction_payload(
            amount=payload.amount,
            ewma_mean=payload.user_historical_mean,
            ewma_var=payload.user_historical_var,
            user_history_count=payload.user_history_count,
            device_fingerprint=payload.device_fingerprint
        )

        rule_results = await rule_eval_task

        rule_score = rule_results.get("rule_risk_score", 0.0)
        anomaly_score = anomaly_results.get("composite_anomaly_score", 0.0)

        final_risk = min(1.0, 0.50 * rule_score + 0.50 * anomaly_score)

        if final_risk <= settings.RISK_THRESHOLD_AUTO_APPROVE:
            decision = "APPROVE"
        elif final_risk >= settings.RISK_THRESHOLD_MANUAL_REVIEW:
            decision = "REJECT"
        else:
            decision = "REVIEW"

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        sla_met = elapsed_ms <= settings.SLA_MAX_LATENCY_MS

        rec, audit_entry = StorageService.save_transaction_verification(
            db=db,
            user_id=payload.user_id,
            amount=payload.amount,
            currency=payload.currency,
            ip_address=payload.ip_address,
            device_fingerprint=payload.device_fingerprint,
            decision=decision,
            risk_score=round(final_risk, 4),
            latency_ms=round(elapsed_ms, 2),
            rules_triggered=rule_results.get("triggered_rules", []),
            anomaly_breakdown=anomaly_results
        )

        event_payload = {
            "id": rec.id,
            "type": "TRANSACTION",
            "name": f"User {rec.id_number_masked}",
            "amount": f"{payload.currency} {payload.amount:,.2f}",
            "decision": decision,
            "risk_score": round(final_risk, 4),
            "latency_ms": round(elapsed_ms, 2),
            "rules_count": len(rule_results.get("triggered_rules", [])),
            "audit_hash": audit_entry.entry_hash[:16] + "...",
            "timestamp": audit_entry.timestamp
        }
        await event_broadcaster.broadcast(event_payload)

        return RiskEvaluationResponse(
            verification_id=rec.id,
            entity_type="TRANSACTION",
            decision=decision,
            risk_score=round(final_risk, 4),
            latency_ms=round(elapsed_ms, 2),
            sla_met=sla_met,
            triggered_rules=rule_results.get("triggered_rules", []),
            anomaly_breakdown=anomaly_results,
            masked_identifiers={
                "user_id": rec.id_number_masked or ""
            },
            audit_hash=audit_entry.entry_hash,
            timestamp=audit_entry.timestamp
        )


verification_pipeline = VerificationPipeline()
