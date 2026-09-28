"""Human-in-the-Loop (HITL) Gatekeeper Node.

Constructs interactive Slack Block Kit payloads and dispatches notifications
to the #ops-approvals channel when risk thresholds are exceeded.
"""

from typing import Dict, Any, List
from core.config import settings
from core.logger import logger
from schemas.ticket import DisputeTicket
from schemas.policy import PolicyEvaluationResult
from schemas.forensics import ComprehensiveForensicsEvidence
from schemas.state import ResolveFlowState


class SlackBlockKitBuilder:
    """Constructs structured Slack Block Kit interactive message cards."""

    @classmethod
    def build_dispute_approval_card(
        cls,
        ticket: DisputeTicket,
        evaluation: PolicyEvaluationResult,
        forensics: ComprehensiveForensicsEvidence,
    ) -> Dict[str, Any]:
        """Creates an interactive Slack message block for operations approval."""
        auspost = forensics.auspost_data
        crm = forensics.customer_data

        delivery_info = "Not Available"
        if auspost:
            delivery_info = f"{auspost.status.value}"
            if auspost.has_signature:
                delivery_info += f" (Signed by {auspost.signature_recipient_name} at {auspost.delivery_suburb})"

        clv_info = f"${crm.lifetime_value_aud:,.2f} AUD ({crm.total_orders_count} orders)" if crm else "New Customer"

        blocks: List[Dict[str, Any]] = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚨 Dispute Approval Required: #{ticket.ticket_id}",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Customer:*\n{ticket.customer_name} (<mailto:{ticket.customer_email}|{ticket.customer_email}>)"},
                    {"type": "mrkdwn", "text": f"*Disputed Amount:*\n*${ticket.amount_aud:,.2f} {ticket.currency}*"},
                    {"type": "mrkdwn", "text": f"*Claim Type:*\n`{ticket.claim_type.value}`"},
                    {"type": "mrkdwn", "text": f"*Customer CLV:*\n{clv_info}"},
                ],
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Australia Post Status:*\n{delivery_info}"},
                    {"type": "mrkdwn", "text": f"*AI Risk Score:*\n*{evaluation.risk_score}/100* ({'HIGH RISK' if evaluation.risk_score >= 70 else 'MODERATE'})"},
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*AI Recommendation:* `{evaluation.recommended_action.value}`\n_{evaluation.reasoning}_",
                },
            },
            {"type": "divider"},
            {
                "type": "actions",
                "block_id": f"approval_actions_{ticket.ticket_id}",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "✅ Approve Refund", "emoji": True},
                        "style": "primary",
                        "value": f'{{"ticket_id": "{ticket.ticket_id}", "thread_id": "{ticket.thread_id}", "action": "FULL_REFUND"}}',
                        "action_id": "btn_approve_refund",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "❌ Reject Dispute", "emoji": True},
                        "style": "danger",
                        "value": f'{{"ticket_id": "{ticket.ticket_id}", "thread_id": "{ticket.thread_id}", "action": "REJECT"}}',
                        "action_id": "btn_reject_dispute",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "ℹ️ Request Info", "emoji": True},
                        "value": f'{{"ticket_id": "{ticket.ticket_id}", "thread_id": "{ticket.thread_id}", "action": "REQUEST_MORE_INFO"}}',
                        "action_id": "btn_request_info",
                    },
                ],
            },
        ]

        return {"channel": settings.SLACK_OPS_CHANNEL, "blocks": blocks}


class HITLGatekeeperAgent:
    """Dispatches Slack approval card when human governance is triggered."""

    @classmethod
    async def dispatch_slack_approval(
        cls,
        ticket: DisputeTicket,
        evaluation: PolicyEvaluationResult,
        forensics: ComprehensiveForensicsEvidence,
    ) -> Dict[str, Any]:
        """Dispatches interactive card to Slack or mock console."""
        slack_payload = SlackBlockKitBuilder.build_dispute_approval_card(
            ticket=ticket, evaluation=evaluation, forensics=forensics
        )

        logger.info(
            "hitl_slack_card_dispatched",
            ticket_id=ticket.ticket_id,
            channel=settings.SLACK_OPS_CHANNEL,
            mock_mode=settings.SLACK_MOCK_MODE,
        )

        return {
            "slack_message_ts": f"mock_ts_{ticket.ticket_id}",
            "slack_channel_id": settings.SLACK_OPS_CHANNEL,
            "card_payload": slack_payload,
        }


async def hitl_gatekeeper_node(state: ResolveFlowState) -> Dict[str, Any]:
    """LangGraph node wrapper for HITL Gatekeeper."""
    ticket = state["ticket"]
    evaluation = state["policy_evaluation"]
    forensics = state["forensics"]

    slack_info = await HITLGatekeeperAgent.dispatch_slack_approval(ticket, evaluation, forensics)
    execution_path = state.get("execution_path", []) + ["hitl_gatekeeper_node"]

    return {
        "slack_message_ts": slack_info["slack_message_ts"],
        "slack_channel_id": slack_info["slack_channel_id"],
        "execution_path": execution_path,
    }
