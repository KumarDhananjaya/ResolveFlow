"""Unit tests for the Settlement & Customer Communication Agent."""

import pytest
from agents.settlement_agent import SettlementAgent, settlement_node
from schemas.ticket import DisputeTicket, ClaimType
from schemas.policy import PolicyEvaluationResult, RecommendedAction, HumanReviewDecision
from schemas.state import ResolveFlowState


@pytest.mark.asyncio
async def test_settlement_refund_execution():
    ticket = DisputeTicket(
        ticket_id="DISP-SETTLE-01",
        thread_id="thread_settle01",
        customer_email="jane@example.com.au",
        customer_name="Jane Doe",
        transaction_id="ch_SAFE_UNDER_100",
        amount_aud=49.95,
        claim_type=ClaimType.ITEM_NOT_RECEIVED,
        sanitized_notes="Lost item",
    )
    evaluation = PolicyEvaluationResult(
        risk_score=20,
        recommended_action=RecommendedAction.FULL_REFUND,
        refund_amount_aud=49.95,
        reasoning="Lost in transit",
    )

    res = await SettlementAgent.execute_settlement(ticket, evaluation)
    assert res["settlement_status"] == "REFUNDED"
    assert res["final_amount_refunded_aud"] == 49.95
    assert "re_" in res["refund_id"]
    assert "processed back to your original payment method" in res["customer_communication_draft"]


@pytest.mark.asyncio
async def test_settlement_rejection_letter():
    ticket = DisputeTicket(
        ticket_id="DISP-SETTLE-02",
        thread_id="thread_settle02",
        customer_email="bad@actor.net",
        customer_name="Bob Scammer",
        transaction_id="ch_HIGH_RISK_FRAUD",
        amount_aud=850.00,
        claim_type=ClaimType.ITEM_NOT_RECEIVED,
        sanitized_notes="Claim",
    )
    evaluation = PolicyEvaluationResult(
        risk_score=85,
        recommended_action=RecommendedAction.REJECT,
        refund_amount_aud=0.0,
        reasoning="Delivered with signature",
    )

    res = await SettlementAgent.execute_settlement(ticket, evaluation)
    assert res["settlement_status"] == "SETTLED_NO_REFUND"
    assert res["refund_id"] is None
    assert "unable to approve a refund" in res["customer_communication_draft"]
