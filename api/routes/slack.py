"""Slack Block Kit interactive webhook listener and LangGraph state resumption."""

import json
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Form
from core.logger import logger
from schemas.policy import HumanReviewDecision, RecommendedAction
from agents.graph import dispute_resolution_graph

router = APIRouter(prefix="/slack", tags=["Slack Integration"])


@router.post("/interactions", summary="Receive Slack interactive card button clicks")
async def handle_slack_interaction(payload: str = Form(...)) -> Dict[str, Any]:
    """Receives Slack Block Kit button clicks, updates LangGraph state, and resumes execution."""
    try:
        data = json.loads(payload)
    except Exception as e:
        logger.error("slack_payload_json_decode_error", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    user_info = data.get("user", {})
    reviewer_id = user_info.get("id", "U_UNKNOWN")
    reviewer_name = user_info.get("username", "Operations Manager")

    actions = data.get("actions", [])
    if not actions:
        return {"status": "ignored_no_action"}

    first_action = actions[0]
    action_value_str = first_action.get("value")

    try:
        action_val = json.loads(action_value_str)
        ticket_id = action_val.get("ticket_id")
        thread_id = action_val.get("thread_id")
        raw_decision = action_val.get("action", "REJECT")
    except Exception as e:
        logger.error("slack_action_value_parse_error", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid action value format")

    logger.info(
        "slack_interaction_received",
        ticket_id=ticket_id,
        thread_id=thread_id,
        decision=raw_decision,
        reviewer=reviewer_name,
    )

    decision_enum = RecommendedAction(raw_decision)
    human_decision = HumanReviewDecision(
        decision=decision_enum,
        reviewer_id=reviewer_id,
        reviewer_name=reviewer_name,
        reviewed_at=datetime.utcnow().isoformat(),
        notes=f"Reviewed via Slack interactive card by {reviewer_name}",
    )

    config = {"configurable": {"thread_id": thread_id}}

    # Update paused graph state with human decision
    dispute_resolution_graph.update_state(
        config,
        {"human_decision": human_decision},
        as_node="hitl_gatekeeper_node",
    )

    # Resume graph execution past the breakpoint
    resumed_state = await dispute_resolution_graph.ainvoke(None, config=config)

    logger.info(
        "graph_resumed_and_completed",
        ticket_id=ticket_id,
        thread_id=thread_id,
        settlement_status=resumed_state.get("settlement_status"),
    )

    return {
        "response_type": "ephemeral",
        "text": f"✅ Dispute *#{ticket_id}* decision recorded as *{decision_enum.value}* by {reviewer_name}. Graph resumed and settled!",
        "settlement_status": resumed_state.get("settlement_status"),
        "refund_id": resumed_state.get("refund_id"),
        "final_amount_refunded_aud": resumed_state.get("final_amount_refunded_aud"),
    }
