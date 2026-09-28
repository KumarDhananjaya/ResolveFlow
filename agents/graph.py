"""LangGraph Multi-Agent StateGraph Assembly.

Wires together the 5 autonomous agents with conditional routing:
- Triage -> Forensics -> Policy Evaluation
- Policy -> Check if HITL needed:
    - If YES -> HITL Gatekeeper -> [INTERRUPT before Settlement Node]
    - If NO -> Direct to Settlement Node -> END
"""

from typing import Literal, Dict, Any
from langgraph.graph import StateGraph, END
from schemas.state import ResolveFlowState
from agents.triage_agent import triage_node
from agents.forensics_agent import forensics_node
from agents.policy_agent import policy_node
from agents.hitl_gatekeeper import hitl_gatekeeper_node
from agents.settlement_agent import settlement_node
from core.checkpointer import get_checkpointer
from core.logger import logger


def route_after_policy(state: ResolveFlowState) -> Literal["hitl_gatekeeper_node", "settlement_node"]:
    """Conditional router determining whether human approval is required."""
    policy_eval = state.get("policy_evaluation")
    if policy_eval and policy_eval.requires_human_approval:
        logger.info("routing_to_hitl_gatekeeper", triggers=policy_eval.hitl_trigger_reasons)
        return "hitl_gatekeeper_node"
    
    logger.info("routing_directly_to_settlement", action=policy_eval.recommended_action if policy_eval else "unknown")
    return "settlement_node"


def create_dispute_graph(enable_interrupt: bool = True):
    """Assembles and compiles the ResolveFlow Multi-Agent LangGraph."""
    workflow = StateGraph(ResolveFlowState)

    # Add agent nodes
    workflow.add_node("triage_node", triage_node)
    workflow.add_node("forensics_node", forensics_node)
    workflow.add_node("policy_node", policy_node)
    workflow.add_node("hitl_gatekeeper_node", hitl_gatekeeper_node)
    workflow.add_node("settlement_node", settlement_node)

    # Set entry point
    workflow.set_entry_point("triage_node")

    # Connect nodes
    workflow.add_edge("triage_node", "forensics_node")
    workflow.add_edge("forensics_node", "policy_node")

    # Conditional routing after policy evaluation
    workflow.add_conditional_edges(
        "policy_node",
        route_after_policy,
        {
            "hitl_gatekeeper_node": "hitl_gatekeeper_node",
            "settlement_node": "settlement_node",
        },
    )

    workflow.add_edge("hitl_gatekeeper_node", "settlement_node")
    workflow.add_edge("settlement_node", END)

    checkpointer = get_checkpointer()

    interrupt_nodes = ["settlement_node"] if enable_interrupt else []
    app = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=interrupt_nodes,
    )
    return app


# Singleton compiled graph instance
dispute_resolution_graph = create_dispute_graph(enable_interrupt=True)
