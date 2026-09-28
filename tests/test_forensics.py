"""Unit tests for the Forensics & Evidence Gathering Agent."""

import pytest
from agents.forensics_agent import ForensicsAgent, forensics_node
from schemas.ticket import DisputeTicket, ClaimType
from schemas.forensics import DeliveryStatus, PaymentStatus
from schemas.state import ResolveFlowState


@pytest.mark.asyncio
async def test_forensics_agent_full_investigation():
    ticket = DisputeTicket(
        ticket_id="DISP-TEST01",
        thread_id="thread_test01",
        customer_email="jane.doe@example.com.au",
        customer_name="Jane Doe",
        transaction_id="ch_3N8au82eZvKYlo2C1g9X8xYz",
        tracking_number="AP982347102AU",
        amount_aud=285.00,
        claim_type=ClaimType.ITEM_NOT_RECEIVED,
        sanitized_notes="Never received package.",
    )

    evidence = await ForensicsAgent.investigate(ticket)
    assert evidence.ticket_id == "DISP-TEST01"
    assert evidence.auspost_data is not None
    assert evidence.auspost_data.status == DeliveryStatus.DELIVERED
    assert evidence.auspost_data.has_signature is True
    assert evidence.stripe_data is not None
    assert evidence.stripe_data.payment_status == PaymentStatus.SUCCEEDED
    assert evidence.customer_data is not None
    assert evidence.customer_data.vip_status is True
    assert len(evidence.anomalies_detected) > 0


@pytest.mark.asyncio
async def test_forensics_node_execution():
    ticket = DisputeTicket(
        ticket_id="DISP-TEST02",
        thread_id="thread_test02",
        customer_email="bad.actor@fraudster.net",
        customer_name="Bob Scammer",
        transaction_id="ch_HIGH_RISK_FRAUD",
        tracking_number=None,
        amount_aud=850.00,
        claim_type=ClaimType.UNAUTHORIZED_TRANSACTION,
        sanitized_notes="Fraud claim",
    )
    state: ResolveFlowState = {
        "ticket": ticket,
        "execution_path": ["triage_node"],
    }
    output = await forensics_node(state)
    assert "forensics" in output
    assert output["execution_path"] == ["triage_node", "forensics_node"]
    assert any("chargeback velocity" in anomaly.lower() for anomaly in output["forensics"].anomalies_detected)
