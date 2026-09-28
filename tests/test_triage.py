"""Unit tests for the Intake & Triage Agent."""

import pytest
from agents.triage_agent import TriageAgent, triage_node
from schemas.ticket import DisputeTicketInput, ClaimType
from schemas.state import ResolveFlowState


@pytest.mark.asyncio
async def test_triage_agent_explicit_claim():
    raw_input = DisputeTicketInput(
        customer_email="jane.doe@example.com.au",
        transaction_id="ch_123456",
        tracking_number="AP982347102AU",
        amount_aud=285.00,
        claim_type=ClaimType.ITEM_NOT_RECEIVED,
        evidence_notes="Parcel was never delivered to my Melbourne house.",
    )
    ticket = await TriageAgent.process(raw_input)
    assert ticket.customer_email == "jane.doe@example.com.au"
    assert ticket.claim_type == ClaimType.ITEM_NOT_RECEIVED
    assert ticket.amount_aud == 285.00
    assert ticket.ticket_id.startswith("DISP-")


@pytest.mark.asyncio
async def test_triage_agent_inferred_claim():
    raw_input = DisputeTicketInput(
        customer_email="john@example.com.au",
        transaction_id="ch_888999",
        amount_aud=55.00,
        claim_type=ClaimType.OTHER,
        evidence_notes="I was charged twice on my statement for the same coffee order.",
    )
    ticket = await TriageAgent.process(raw_input)
    assert ticket.claim_type == ClaimType.DUPLICATE_CHARGE


@pytest.mark.asyncio
async def test_triage_node_state_transformation():
    state: ResolveFlowState = {
        "raw_input": DisputeTicketInput(
            customer_email="alex@company.com.au",
            transaction_id="ch_999111",
            amount_aud=120.00,
            claim_type=ClaimType.DAMAGED_GOODS,
            evidence_notes="Item arrived broken and smashed in box.",
        ),
        "execution_path": [],
    }
    output = await triage_node(state)
    assert "ticket" in output
    assert output["execution_path"] == ["triage_node"]
    assert output["ticket"].claim_type == ClaimType.DAMAGED_GOODS
