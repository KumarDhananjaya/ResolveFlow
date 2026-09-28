"""Dispute ingestion and status management endpoints."""

import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from core.logger import logger
from schemas.ticket import DisputeTicketInput
from schemas.state import ResolveFlowState
from agents.graph import dispute_resolution_graph

router = APIRouter(prefix="/disputes", tags=["Disputes"])


@router.post("/ingest", summary="Ingest raw customer dispute ticket")
async def ingest_dispute_ticket(payload: DisputeTicketInput) -> Dict[str, Any]:
    """Ingests a customer dispute and initiates autonomous multi-agent resolution."""
    thread_id = f"thread_{uuid.uuid4().hex[:8]}"
    logger.info("api_ingesting_dispute", email=payload.customer_email, tx_id=payload.transaction_id, thread_id=thread_id)

    initial_state: ResolveFlowState = {
        "raw_input": payload,
        "thread_id": thread_id,
        "ticket_id": "",
        "execution_path": [],
        "metadata": {"source": "fastapi_rest_ingest"},
    }

    config = {"configurable": {"thread_id": thread_id}}

    try:
        # Run graph until completion or HITL breakpoint interrupt
        state_output = await dispute_resolution_graph.ainvoke(initial_state, config=config)
        
        # Check if the graph paused at a breakpoint
        snapshot = dispute_resolution_graph.get_state(config)
        is_interrupted = len(snapshot.next) > 0 if snapshot else False

        ticket = state_output.get("ticket")
        policy = state_output.get("policy_evaluation")

        return {
            "status": "PAUSED_PENDING_APPROVAL" if is_interrupted else "SETTLED",
            "thread_id": thread_id,
            "ticket_id": ticket.ticket_id if ticket else "UNKNOWN",
            "is_interrupted": is_interrupted,
            "next_node": list(snapshot.next) if is_interrupted else [],
            "risk_score": policy.risk_score if policy else None,
            "recommended_action": policy.recommended_action.value if policy else None,
            "requires_human_approval": policy.requires_human_approval if policy else False,
            "settlement_status": state_output.get("settlement_status"),
            "refund_id": state_output.get("refund_id"),
            "final_amount_refunded_aud": state_output.get("final_amount_refunded_aud"),
            "execution_path": state_output.get("execution_path", []),
        }

    except Exception as e:
        logger.error("api_dispute_ingest_failed", error=str(e), thread_id=thread_id)
        raise HTTPException(status_code=500, detail=f"Dispute processing failed: {str(e)}")


@router.get("/{thread_id}/state", summary="Query dispute execution graph state")
async def get_dispute_state(thread_id: str) -> Dict[str, Any]:
    """Retrieves current checkpoint state and execution snapshot for a dispute thread."""
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = dispute_resolution_graph.get_state(config)

    if not snapshot or not snapshot.values:
        raise HTTPException(status_code=404, detail="Dispute thread not found or expired")

    state_values = snapshot.values
    return {
        "thread_id": thread_id,
        "is_paused": len(snapshot.next) > 0,
        "next_nodes": list(snapshot.next),
        "ticket": state_values.get("ticket"),
        "policy_evaluation": state_values.get("policy_evaluation"),
        "settlement_status": state_values.get("settlement_status"),
        "refund_id": state_values.get("refund_id"),
        "execution_path": state_values.get("execution_path", []),
    }
