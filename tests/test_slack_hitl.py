"""Unit tests for the Human-in-the-Loop Slack Block Kit builder and dispatcher."""

import pytest
import json
from agents.hitl_gatekeeper import SlackBlockKitBuilder, HITLGatekeeperAgent
from schemas.ticket import DisputeTicket, ClaimType
from schemas.policy import PolicyEvaluationResult, RecommendedAction
from schemas.forensics import ComprehensiveForensicsEvidence, AusPostForensics, DeliveryStatus


@pytest.mark.asyncio
async def test_slack_block_kit_structure():
    ticket = DisputeTicket(
        ticket_id="DISP-SLACK-01",
        thread_id="thread_slack01",
        customer_email="jane@example.com.au",
        customer_name="Jane Doe",
        transaction_id="ch_123",
        amount_aud=285.00,
        claim_type=ClaimType.ITEM_NOT_RECEIVED,
        sanitized_notes="Never arrived",
    )
    evaluation = PolicyEvaluationResult(
        risk_score=75,
        recommended_action=RecommendedAction.REJECT,
        reasoning="Signed delivery proof",
        requires_human_approval=True,
    )
    forensics = ComprehensiveForensicsEvidence(
        ticket_id="DISP-SLACK-01",
        auspost_data=AusPostForensics(
            tracking_number="AP123",
            status=DeliveryStatus.DELIVERED,
            has_signature=True,
            signature_recipient_name="J. Doe",
            delivery_suburb="Melbourne",
        ),
    )

    card = SlackBlockKitBuilder.build_dispute_approval_card(ticket, evaluation, forensics)
    assert "blocks" in card
    blocks = card["blocks"]
    
    # Check header block
    assert blocks[0]["type"] == "header"
    assert "DISP-SLACK-01" in blocks[0]["text"]["text"]

    # Check action buttons
    action_block = next(b for b in blocks if b["type"] == "actions")
    assert len(action_block["elements"]) == 3
    approve_btn = action_block["elements"][0]
    btn_val = json.loads(approve_btn["value"])
    assert btn_val["ticket_id"] == "DISP-SLACK-01"
    assert btn_val["action"] == "FULL_REFUND"


@pytest.mark.asyncio
async def test_hitl_agent_dispatch():
    ticket = DisputeTicket(
        ticket_id="DISP-SLACK-02",
        thread_id="thread_slack02",
        customer_email="alex@example.com.au",
        customer_name="Alex Smith",
        transaction_id="ch_456",
        amount_aud=350.00,
        claim_type=ClaimType.UNAUTHORIZED_TRANSACTION,
        sanitized_notes="Stolen card",
    )
    evaluation = PolicyEvaluationResult(
        risk_score=80,
        recommended_action=RecommendedAction.REJECT,
        reasoning="High chargeback velocity",
        requires_human_approval=True,
    )
    forensics = ComprehensiveForensicsEvidence(ticket_id="DISP-SLACK-02")

    res = await HITLGatekeeperAgent.dispatch_slack_approval(ticket, evaluation, forensics)
    assert "mock_ts_" in res["slack_message_ts"]
    assert res["slack_channel_id"] is not None
