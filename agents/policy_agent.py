"""Risk and Policy Evaluator Agent.

Evaluates dispute facts and forensics against internal corporate policy,
computes a deterministic risk score (0-100), and formulates recommendations.
"""

from typing import Dict, Any, List
from core.config import settings
from core.logger import logger
from schemas.ticket import DisputeTicket, ClaimType
from schemas.forensics import ComprehensiveForensicsEvidence, DeliveryStatus
from schemas.policy import (
    PolicyEvaluationResult,
    RecommendedAction,
    PolicyRuleMatch,
)
from schemas.state import ResolveFlowState


class PolicyEvaluatorAgent:
    """Agent that calculates risk scores and applies the corporate dispute matrix."""

    @classmethod
    def evaluate(
        cls,
        ticket: DisputeTicket,
        forensics: ComprehensiveForensicsEvidence,
    ) -> PolicyEvaluationResult:
        """Evaluates policy rules and determines whether human escalation is mandated."""
        logger.info("policy_agent_evaluating", ticket_id=ticket.ticket_id, amount=ticket.amount_aud)

        risk_score = 10  # Baseline low risk
        rule_matches: List[PolicyRuleMatch] = []
        hitl_triggers: List[str] = []

        auspost = forensics.auspost_data
        stripe = forensics.stripe_data
        crm = forensics.customer_data

        # Rule 1: Signed delivery proof verification
        if ticket.claim_type == ClaimType.ITEM_NOT_RECEIVED:
            if auspost and auspost.status == DeliveryStatus.DELIVERED and auspost.has_signature:
                risk_score += 65
                rule_matches.append(
                    PolicyRuleMatch(
                        rule_id="RULE-POD-01",
                        rule_name="Signature on Delivery Match",
                        passed=False,
                        risk_impact=65,
                        description=f"Carrier confirmed delivery with signature to {auspost.delivery_suburb} {auspost.delivery_postcode}.",
                    )
                )
            elif auspost and auspost.status == DeliveryStatus.FAILED_ATTEMPT:
                risk_score -= 5
                rule_matches.append(
                    PolicyRuleMatch(
                        rule_id="RULE-POD-02",
                        rule_name="Postal Delivery Failed/Returned",
                        passed=True,
                        risk_impact=-5,
                        description="Carrier confirmed parcel was not successfully delivered.",
                    )
                )

        # Rule 2: Chargeback velocity
        if crm and crm.chargeback_count_60d >= settings.MAX_ALLOWED_CHARGEBACKS_60D:
            risk_score += 40
            rule_matches.append(
                PolicyRuleMatch(
                    rule_id="RULE-CB-01",
                    rule_name="Elevated Chargeback Frequency",
                    passed=False,
                    risk_impact=40,
                    description=f"Customer has {crm.chargeback_count_60d} chargebacks in 60 days.",
                )
            )

        # Rule 3: Customer Lifetime Value (CLV) & VIP trust bonus
        if crm and crm.vip_status and crm.lifetime_value_aud > 2000.0:
            risk_score = max(0, risk_score - 20)
            rule_matches.append(
                PolicyRuleMatch(
                    rule_id="RULE-VIP-01",
                    rule_name="VIP High CLV Relationship",
                    passed=True,
                    risk_impact=-20,
                    description=f"High customer value (${crm.lifetime_value_aud:,.2f} AUD).",
                )
            )

        # Cap risk score between 0 and 100
        final_risk_score = min(100, max(0, risk_score))

        # Check financial and risk thresholds
        if ticket.amount_aud > settings.DISPUTE_AUTO_REFUND_THRESHOLD_AUD:
            hitl_triggers.append(
                f"Disputed amount (${ticket.amount_aud:.2f} AUD) exceeds autonomous policy limit (${settings.DISPUTE_AUTO_REFUND_THRESHOLD_AUD:.2f} AUD)."
            )

        if final_risk_score >= settings.HIGH_RISK_SCORE_THRESHOLD:
            hitl_triggers.append(
                f"Elevated Risk Score ({final_risk_score}/100 exceeds threshold {settings.HIGH_RISK_SCORE_THRESHOLD})."
            )

        # Formulate recommendation
        if final_risk_score >= 70:
            recommended_action = RecommendedAction.REJECT
            refund_amount = 0.0
            reasoning = f"Forensic analysis detected strong delivery confirmation or elevated fraud risk (Risk Score: {final_risk_score}/100). AI recommends rejecting the dispute."
        elif final_risk_score <= 30:
            recommended_action = RecommendedAction.FULL_REFUND
            refund_amount = ticket.amount_aud
            reasoning = f"Low risk claim with legitimate delivery failure or verified merchant error (Risk Score: {final_risk_score}/100). AI recommends full refund."
        else:
            recommended_action = RecommendedAction.PARTIAL_REFUND
            refund_amount = round(ticket.amount_aud * 0.5, 2)
            reasoning = f"Moderate risk dispute with ambiguous evidence (Risk Score: {final_risk_score}/100). AI recommends 50% partial settlement."

        requires_hitl = len(hitl_triggers) > 0

        result = PolicyEvaluationResult(
            risk_score=final_risk_score,
            recommended_action=recommended_action,
            refund_amount_aud=refund_amount,
            reasoning=reasoning,
            rule_matches=rule_matches,
            requires_human_approval=requires_hitl,
            hitl_trigger_reasons=hitl_triggers,
        )

        logger.info(
            "policy_agent_completed",
            risk_score=final_risk_score,
            action=recommended_action,
            requires_hitl=requires_hitl,
        )
        return result


async def policy_node(state: ResolveFlowState) -> Dict[str, Any]:
    """LangGraph node wrapper for Policy Agent."""
    ticket = state["ticket"]
    forensics = state["forensics"]
    evaluation = PolicyEvaluatorAgent.evaluate(ticket, forensics)
    
    execution_path = state.get("execution_path", []) + ["policy_node"]
    return {
        "policy_evaluation": evaluation,
        "execution_path": execution_path,
    }
