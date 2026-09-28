"""Forensics and Evidence Gathering Agent.

Orchestrates concurrent retrieval of logistics milestones (Australia Post),
payment ledger forensics (Stripe), and historical customer profile data (CRM).
Detects factual discrepancies and compiles comprehensive dispute proof.
"""

import asyncio
from typing import Dict, Any, List
from core.logger import logger
from schemas.ticket import DisputeTicket
from schemas.forensics import (
    ComprehensiveForensicsEvidence,
    AusPostForensics,
    StripeForensics,
    CustomerLedgerForensics,
    DeliveryStatus,
)
from schemas.state import ResolveFlowState
from tools.auspost_tool import AustraliaPostTool
from tools.stripe_tool import StripePaymentTool
from tools.crm_tool import CRMLedgerTool


class ForensicsAgent:
    """Investigates transaction legitimacy across payment, postal, and customer systems."""

    @classmethod
    async def investigate(cls, ticket: DisputeTicket) -> ComprehensiveForensicsEvidence:
        """Executes parallel forensic queries across Australia Post, Stripe, and CRM."""
        logger.info("forensics_agent_investigating", ticket_id=ticket.ticket_id, tx_id=ticket.transaction_id)

        # Run external tools concurrently
        auspost_task = AustraliaPostTool.get_delivery_proof(ticket.tracking_number)
        stripe_task = StripePaymentTool.get_transaction_status(ticket.transaction_id)
        crm_task = CRMLedgerTool.get_customer_history(ticket.customer_email)

        auspost_res, stripe_res, crm_res = await asyncio.gather(
            auspost_task, stripe_task, crm_task, return_exceptions=False
        )

        anomalies: List[str] = []

        # Cross-system discrepancy analysis
        if auspost_res.status == DeliveryStatus.DELIVERED and auspost_res.has_signature:
            anomalies.append(
                f"Delivered with signature proof to {auspost_res.delivery_suburb} {auspost_res.delivery_postcode} by '{auspost_res.signature_recipient_name}'."
            )

        if crm_res.chargeback_count_60d >= 3:
            anomalies.append(
                f"High chargeback velocity: Customer filed {crm_res.chargeback_count_60d} chargebacks in the last 60 days."
            )

        if stripe_res.disputed:
            anomalies.append("Cardholder has already initiated a formal chargeback on payment rails.")

        evidence = ComprehensiveForensicsEvidence(
            ticket_id=ticket.ticket_id,
            auspost_data=auspost_res,
            stripe_data=stripe_res,
            customer_data=crm_res,
            anomalies_detected=anomalies,
        )

        logger.info(
            "forensics_agent_completed",
            ticket_id=ticket.ticket_id,
            anomalies_count=len(anomalies),
            delivery_status=auspost_res.status,
        )
        return evidence


async def forensics_node(state: ResolveFlowState) -> Dict[str, Any]:
    """LangGraph node wrapper for Forensics Agent."""
    ticket = state["ticket"]
    evidence = await ForensicsAgent.investigate(ticket)
    
    execution_path = state.get("execution_path", []) + ["forensics_node"]
    return {
        "forensics": evidence,
        "execution_path": execution_path,
    }
