"""Intake and Triage Agent.

Responsible for ingesting raw customer communications (emails, Zendesk tickets, API payloads),
sanitizing PII in compliance with the Australian Privacy Principles (APP), and converting
unstructured text into a validated Pydantic DisputeTicket model.
"""

import uuid
from typing import Dict, Any, Optional
from core.logger import logger
from core.security import PIISanitizer
from schemas.ticket import DisputeTicket, DisputeTicketInput, ClaimType
from schemas.state import ResolveFlowState


class TriageAgent:
    """Agent responsible for dispute intake, intent recognition, and schema validation."""

    @staticmethod
    def infer_claim_type(evidence_notes: str) -> ClaimType:
        """Infers the claim type from customer complaint text when not explicitly provided."""
        text_lower = evidence_notes.lower()
        if any(w in text_lower for w in ["never arrived", "not received", "didn't receive", "where is my parcel", "missing package"]):
            return ClaimType.ITEM_NOT_RECEIVED
        elif any(w in text_lower for w in ["unauthorized", "fraud", "scam", "stolen card", "didn't authorize"]):
            return ClaimType.UNAUTHORIZED_TRANSACTION
        elif any(w in text_lower for w in ["damaged", "broken", "faulty", "smashed", "defective"]):
            return ClaimType.DAMAGED_GOODS
        elif any(w in text_lower for w in ["charged twice", "double charge", "duplicate"]):
            return ClaimType.DUPLICATE_CHARGE
        elif any(w in text_lower for w in ["wrong amount", "overcharged", "incorrect price"]):
            return ClaimType.INCORRECT_AMOUNT
        elif any(w in text_lower for w in ["cancelled subscription", "still charging me", "recurring"]):
            return ClaimType.SUBSCRIPTION_CANCELLED
        return ClaimType.OTHER

    @classmethod
    async def process(cls, raw_input: DisputeTicketInput, thread_id: Optional[str] = None) -> DisputeTicket:
        """Processes raw input, scrubs PII, and returns a structured DisputeTicket."""
        logger.info("triage_agent_processing_ticket", email=raw_input.customer_email, tx_id=raw_input.transaction_id)

        # Sanitize PII in evidence notes
        sanitized_notes = PIISanitizer.sanitize_text(raw_input.evidence_notes)

        # Infer claim type if default or ambiguous
        claim_type = raw_input.claim_type
        if claim_type == ClaimType.OTHER or not claim_type:
            claim_type = cls.infer_claim_type(raw_input.evidence_notes)

        ticket_id = f"DISP-{uuid.uuid4().hex[:6].upper()}"
        assigned_thread_id = thread_id or f"thread_{ticket_id}"

        ticket = DisputeTicket(
            ticket_id=ticket_id,
            thread_id=assigned_thread_id,
            customer_email=raw_input.customer_email,
            customer_name=raw_input.customer_name or "Customer",
            transaction_id=raw_input.transaction_id,
            tracking_number=raw_input.tracking_number,
            amount_aud=raw_input.amount_aud,
            currency="AUD",
            claim_type=claim_type,
            sanitized_notes=sanitized_notes,
            metadata={"sanitized": True, "triage_version": "2.0"},
        )

        logger.info("triage_agent_completed", ticket_id=ticket.ticket_id, claim_type=ticket.claim_type)
        return ticket


async def triage_node(state: ResolveFlowState) -> Dict[str, Any]:
    """LangGraph node wrapper for Triage Agent."""
    raw_input = state["raw_input"]
    thread_id = state.get("thread_id")
    ticket = await TriageAgent.process(raw_input, thread_id=thread_id)
    
    execution_path = state.get("execution_path", []) + ["triage_node"]
    return {
        "ticket": ticket,
        "ticket_id": ticket.ticket_id,
        "thread_id": ticket.thread_id,
        "execution_path": execution_path,
    }
