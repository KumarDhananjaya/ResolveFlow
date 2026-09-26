"""Tests for Pydantic v2 schemas and data validation."""

import pytest
from pydantic import ValidationError
from schemas.ticket import DisputeTicketInput, ClaimType
from schemas.policy import PolicyEvaluationResult, RecommendedAction


def test_dispute_ticket_validation():
    valid_ticket = DisputeTicketInput(
        customer_email="jane@example.com.au",
        transaction_id="ch_12345678",
        amount_aud=129.505,
        claim_type=ClaimType.ITEM_NOT_RECEIVED,
        evidence_notes="Goods not received at Melbourne warehouse.",
    )
    assert valid_ticket.amount_aud == 129.51
    assert valid_ticket.claim_type == ClaimType.ITEM_NOT_RECEIVED


def test_dispute_ticket_negative_amount_fails():
    with pytest.raises(ValidationError):
        DisputeTicketInput(
            customer_email="jane@example.com.au",
            transaction_id="ch_12345678",
            amount_aud=-10.0,
            claim_type=ClaimType.ITEM_NOT_RECEIVED,
            evidence_notes="Negative amount test",
        )


def test_policy_evaluation_schema():
    eval_result = PolicyEvaluationResult(
        risk_score=85,
        recommended_action=RecommendedAction.REJECT,
        refund_amount_aud=0.0,
        reasoning="Australia Post signature matches recipient name.",
        requires_human_approval=True,
        hitl_trigger_reasons=["High Risk Score (85 > 70)"],
    )
    assert eval_result.risk_score == 85
    assert eval_result.recommended_action == RecommendedAction.REJECT
    assert eval_result.requires_human_approval is True
