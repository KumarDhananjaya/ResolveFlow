"""End-to-End Tests for LangGraph Multi-Agent StateGraph Workflow."""

import pytest
from schemas.ticket import DisputeTicketInput, ClaimType
from schemas.policy import HumanReviewDecision, RecommendedAction
from schemas.state import ResolveFlowState
from agents.graph import create_dispute_graph
from core.checkpointer import reset_checkpointer


@pytest.mark.asyncio
async def test_graph_auto_resolution_low_value():
    reset_checkpointer()
    graph = create_dispute_graph(enable_interrupt=True)
    
    payload = DisputeTicketInput(
        customer_email="alex@gmail.com",
        customer_name="Alex Smith",
        transaction_id="ch_SAFE_UNDER_100",
        tracking_number="AP_LOST_002",
        amount_aud=49.95,
        claim_type=ClaimType.ITEM_NOT_RECEIVED,
        evidence_notes="Parcel was lost in transit and never arrived.",
    )
    
    thread_id = "thread_test_auto_01"
    initial_state: ResolveFlowState = {
        "raw_input": payload,
        "thread_id": thread_id,
        "execution_path": [],
    }
    
    config = {"configurable": {"thread_id": thread_id}}
    final_state = await graph.ainvoke(initial_state, config=config)
    
    # Check that it went directly from policy to settlement without interrupt
    assert "settlement_node" in final_state["execution_path"]
    assert final_state["settlement_status"] == "REFUNDED"
    assert final_state["final_amount_refunded_aud"] == 49.95


@pytest.mark.asyncio
async def test_graph_interrupt_and_resume_on_high_value():
    reset_checkpointer()
    graph = create_dispute_graph(enable_interrupt=True)

    payload = DisputeTicketInput(
        customer_email="jane.doe@example.com.au",
        customer_name="Jane Doe",
        transaction_id="ch_3N8au82eZvKYlo2C1g9X8xYz",
        tracking_number="AP982347102AU",
        amount_aud=285.00,
        claim_type=ClaimType.ITEM_NOT_RECEIVED,
        evidence_notes="Goods not received at Melbourne.",
    )

    thread_id = "thread_test_hitl_02"
    initial_state: ResolveFlowState = {
        "raw_input": payload,
        "thread_id": thread_id,
        "execution_path": [],
    }

    config = {"configurable": {"thread_id": thread_id}}
    
    # 1. Run until breakpoint
    state_paused = await graph.ainvoke(initial_state, config=config)
    snapshot = graph.get_state(config)
    
    # Graph should be paused at settlement_node
    assert "settlement_node" in list(snapshot.next)
    assert "hitl_gatekeeper_node" in state_paused["execution_path"]

    # 2. Simulate human manager rejecting the dispute via Slack
    human_decision = HumanReviewDecision(
        decision=RecommendedAction.REJECT,
        reviewer_id="U_OPS_LEAD",
        reviewer_name="Sarah Operations",
        reviewed_at="2026-09-28T10:00:00Z",
        notes="Australia Post confirmed delivery with recipient signature.",
    )

    graph.update_state(config, {"human_decision": human_decision}, as_node="hitl_gatekeeper_node")

    # 3. Resume graph execution past the breakpoint
    resumed_state = await graph.ainvoke(None, config=config)

    assert "settlement_node" in resumed_state["execution_path"]
    assert resumed_state["settlement_status"] == "SETTLED_NO_REFUND"
    assert resumed_state["final_amount_refunded_aud"] == 0.0
