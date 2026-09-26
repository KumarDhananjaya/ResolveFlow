"""LangGraph multi-agent shared state definition for dispute resolution pipeline."""

from typing import TypedDict, Optional, Dict, Any, List
from schemas.ticket import DisputeTicket, DisputeTicketInput
from schemas.forensics import ComprehensiveForensicsEvidence
from schemas.policy import PolicyEvaluationResult, HumanReviewDecision


class ResolveFlowState(TypedDict, total=False):
    """Shared state dictionary passed across all LangGraph nodes."""

    # Thread and tracing identifiers
    thread_id: str
    ticket_id: str

    # 1. Intake / Triage Agent outputs
    raw_input: DisputeTicketInput
    ticket: DisputeTicket

    # 2. Forensics Agent outputs
    forensics: ComprehensiveForensicsEvidence

    # 3. Risk & Policy Agent outputs
    policy_evaluation: PolicyEvaluationResult

    # 4. Human-in-the-Loop Gatekeeper outputs
    human_decision: Optional[HumanReviewDecision]
    slack_message_ts: Optional[str]
    slack_channel_id: Optional[str]

    # 5. Settlement & Communication Agent outputs
    settlement_status: Optional[str]
    refund_id: Optional[str]
    final_amount_refunded_aud: Optional[float]
    customer_communication_draft: Optional[str]
    customer_email_sent: Optional[bool]

    # Execution audit logs and node milestones
    execution_path: List[str]
    error_message: Optional[str]
    metadata: Dict[str, Any]
