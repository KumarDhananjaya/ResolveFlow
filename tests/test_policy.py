"""Unit tests for the Risk & Policy Evaluator Agent."""

import pytest
from datetime import datetime
from agents.policy_agent import PolicyEvaluatorAgent, policy_node
from schemas.ticket import DisputeTicket, ClaimType
from schemas.forensics import (
    ComprehensiveForensicsEvidence,
    AusPostForensics,
    DeliveryStatus,
    StripeForensics,
    PaymentStatus,
    CustomerLedgerForensics,
)
from schemas.policy import RecommendedAction
from schemas.state import ResolveFlowState


@pytest.mark.asyncio
async def test_policy_high_risk_signature_match():
    ticket = DisputeTicket(
        ticket_id="DISP-RISK-01",
        thread_id="thread_risk01",
        customer_email="jane.doe@example.com.au",
        customer_name="Jane Doe",
        transaction_id="ch_123",
        tracking_number="AP982347102AU",
        amount_aud=285.00,
        claim_type=ClaimType.ITEM_NOT_RECEIVED,
        sanitized_notes="Never received goods",
    )
    forensics = ComprehensiveForensicsEvidence(
        ticket_id="DISP-RISK-01",
        auspost_data=AusPostForensics(
            tracking_number="AP982347102AU",
            status=DeliveryStatus.DELIVERED,
            has_signature=True,
            signature_recipient_name="J. Doe",
            delivery_suburb="Melbourne",
            delivery_postcode="3000",
        ),
        customer_data=CustomerLedgerForensics(
            customer_id="cus_1",
            email="jane.doe@example.com.au",
            name="Jane Doe",
            lifetime_value_aud=300.0,
            total_orders_count=2,
            chargeback_count_60d=0,
            trust_score=0.8,
            account_created_at=datetime.utcnow(),
        ),
    )

    evaluation = PolicyEvaluatorAgent.evaluate(ticket, forensics)
    assert evaluation.risk_score >= 70
    assert evaluation.recommended_action == RecommendedAction.REJECT
    assert evaluation.requires_human_approval is True  # > AUD $100 and high risk


@pytest.mark.asyncio
async def test_policy_low_risk_auto_refund():
    ticket = DisputeTicket(
        ticket_id="DISP-SAFE-02",
        thread_id="thread_safe02",
        customer_email="alex@gmail.com",
        customer_name="Alex Smith",
        transaction_id="ch_SAFE_UNDER_100",
        tracking_number="AP_LOST_002",
        amount_aud=49.95,
        claim_type=ClaimType.ITEM_NOT_RECEIVED,
        sanitized_notes="Carrier lost package",
    )
    forensics = ComprehensiveForensicsEvidence(
        ticket_id="DISP-SAFE-02",
        auspost_data=AusPostForensics(
            tracking_number="AP_LOST_002",
            status=DeliveryStatus.FAILED_ATTEMPT,
            has_signature=False,
        ),
        customer_data=CustomerLedgerForensics(
            customer_id="cus_2",
            email="alex@gmail.com",
            name="Alex Smith",
            lifetime_value_aud=50.0,
            total_orders_count=1,
            chargeback_count_60d=0,
            trust_score=0.8,
            account_created_at=datetime.utcnow(),
        ),
    )

    evaluation = PolicyEvaluatorAgent.evaluate(ticket, forensics)
    assert evaluation.risk_score <= 30
    assert evaluation.recommended_action == RecommendedAction.FULL_REFUND
    assert evaluation.requires_human_approval is False  # Safe <= AUD $100 & Low risk
