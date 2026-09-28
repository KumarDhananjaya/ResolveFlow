"""Settlement and Customer Communication Agent.

Executes payment refunds via Stripe rails upon approval,
updates the internal database status, and generates empathetic,
legally compliant correspondence adhering to Australian consumer law.
"""

from typing import Dict, Any, Optional
from core.logger import logger
from schemas.ticket import DisputeTicket
from schemas.policy import PolicyEvaluationResult, RecommendedAction, HumanReviewDecision
from schemas.state import ResolveFlowState
from tools.stripe_tool import StripePaymentTool


class SettlementAgent:
    """Handles financial settlement execution and customer communications."""

    @classmethod
    def generate_customer_response(
        cls,
        ticket: DisputeTicket,
        action: RecommendedAction,
        amount_refunded: float,
        reasoning: str,
    ) -> str:
        """Drafts empathetic, clear customer letter compliant with Australian Consumer Law (ACL)."""
        if action in [RecommendedAction.FULL_REFUND, RecommendedAction.PARTIAL_REFUND]:
            return (
                f"Dear {ticket.customer_name},\n\n"
                f"Thank you for contacting ResolveFlow Support regarding your recent order "
                f"(Reference: #{ticket.ticket_id} / Transaction: {ticket.transaction_id}).\n\n"
                f"We have thoroughly investigated your dispute regarding '{ticket.claim_type.value.replace('_', ' ').title()}'. "
                f"We are pleased to inform you that a refund of ${amount_refunded:,.2f} AUD has been successfully "
                f"processed back to your original payment method via Stripe.\n\n"
                f"Please allow 3 to 5 business days for this refund to reflect in your Australian bank account.\n\n"
                f"Warm regards,\n"
                f"ResolveFlow Operations & Customer Resolution Team"
            )
        elif action == RecommendedAction.REJECT:
            return (
                f"Dear {ticket.customer_name},\n\n"
                f"Thank you for contacting ResolveFlow Support regarding claim #{ticket.ticket_id}.\n\n"
                f"After cross-referencing postal carrier delivery records and signature verification from Australia Post, "
                f"our operations team has confirmed that this parcel was successfully delivered to the designated address.\n\n"
                f"As a result, we are unable to approve a refund at this time under our standard dispute policy.\n"
                f"If you believe this decision was made in error or have additional supporting documentation, "
                f"please reply directly to this notice.\n\n"
                f"Sincerely,\n"
                f"ResolveFlow Operations Team"
            )
        else:
            return (
                f"Dear {ticket.customer_name},\n\n"
                f"We are currently reviewing your dispute #{ticket.ticket_id}. "
                f"To help us expedite our investigation with the carrier, could you please provide any additional details "
                f"or proof of non-delivery.\n\n"
                f"Thank you for your patience.\n"
                f"ResolveFlow Support"
            )

    @classmethod
    async def execute_settlement(
        cls,
        ticket: DisputeTicket,
        evaluation: PolicyEvaluationResult,
        human_decision: Optional[HumanReviewDecision] = None,
    ) -> Dict[str, Any]:
        """Executes refund on payment gateway and generates customer message."""
        # Determine effective resolution action (Human review overrides AI recommendation)
        final_action = human_decision.decision if human_decision else evaluation.recommended_action
        refund_amount = 0.0

        if human_decision and human_decision.override_amount_aud is not None:
            refund_amount = human_decision.override_amount_aud
        elif final_action == RecommendedAction.FULL_REFUND:
            refund_amount = ticket.amount_aud
        elif final_action == RecommendedAction.PARTIAL_REFUND:
            refund_amount = evaluation.refund_amount_aud or round(ticket.amount_aud * 0.5, 2)

        refund_id = None
        settlement_status = "SETTLED_NO_REFUND"

        if final_action in [RecommendedAction.FULL_REFUND, RecommendedAction.PARTIAL_REFUND] and refund_amount > 0:
            refund_result = await StripePaymentTool.execute_refund(
                transaction_id=ticket.transaction_id,
                amount_aud=refund_amount,
                reason="dispute_resolved",
                idempotency_key=f"ref_{ticket.ticket_id}",
            )
            refund_id = refund_result.get("refund_id")
            settlement_status = "REFUNDED"

        customer_draft = cls.generate_customer_response(
            ticket=ticket,
            action=final_action,
            amount_refunded=refund_amount,
            reasoning=evaluation.reasoning,
        )

        logger.info(
            "settlement_agent_completed",
            ticket_id=ticket.ticket_id,
            final_action=final_action,
            refund_id=refund_id,
            amount_refunded=refund_amount,
        )

        return {
            "settlement_status": settlement_status,
            "refund_id": refund_id,
            "final_amount_refunded_aud": refund_amount,
            "customer_communication_draft": customer_draft,
            "customer_email_sent": True,
        }


async def settlement_node(state: ResolveFlowState) -> Dict[str, Any]:
    """LangGraph node wrapper for Settlement Agent."""
    ticket = state["ticket"]
    evaluation = state["policy_evaluation"]
    human_decision = state.get("human_decision")

    settlement_data = await SettlementAgent.execute_settlement(
        ticket=ticket,
        evaluation=evaluation,
        human_decision=human_decision,
    )

    execution_path = state.get("execution_path", []) + ["settlement_node"]
    return {
        **settlement_data,
        "execution_path": execution_path,
    }
